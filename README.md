# AWS Prolific Web-App

## Intro

This web-app was developed in order to deploy studies on the Prolific crowdsourcing platform. It is hosted on the amazon aws platform and supports deployment of similar projects. The back-end code (or serverless functions) is already setup and works across projects. What needs to be setup separately for each project are the database tables and HTML front-end code. This is done via the aws cli that needs to be installed and configured, and via bash shell scripts. To setup a new project you need to be working on a linux machine. 

## Setup
Three things need to be setup: database tables, HMTL front-end and Prolific project. Before moving on to each part, an important thing to remember is that each new project needs to be identified by a unique string, like *studyname* for example. This unique string will need to be inserted during the creation of tables and also in index.html. This string is important because it tells the back-end which project is which.

### Database tables

##### 1. Setup AWS CLI
To be able to manipulate the tables via command line interface the aws cli needs to be set up. Follow the instruction from https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-welcome.html to install and configure the aws cli.

##### 2. Create the tables for the new project

**create_tables.sh** is used  to create the 4 tables: Workers_DB, Batches_DB, Scenarios_DB, Results_DB.
It needs the unique study identifier string as an argument. Let's suppose it's called *studyname*, run the command:

```bash
./create_tables.sh studyname > outputs/output_create_tables.txt
```
"> output_create_tables.txt" is added to supress the output and save to .txt, otherwise each time a table is created you have to go though a man page and then press "q" to exit in order to move on to the next table.

##### 3. Upload scenarios from .csv file to Scenarios_DB table

**upload_scenarios.py** is used to upload the data from the scenarios .csv file to the Scenarios_DB table, it takes the .csv and unique study identifier as arguments. For example, having *studyname* and "scenarios.csv", run:

```bash
python upload_scenarios.py scenarios.csv study_x
```

##### 4. Randomly shuffle batches

**randomize_batches.py** is used to split the scenarios into random evenly sized batches. Optionally a sorting scheme which minimizes similarity between scenarios in the same batch can be applied. Without the sorting scheme the script can run as is, with the sorting scheme enabled the script needs to be adapted to the new project by changing:
- *item_weights*: a list of tuples where each component of the scenario (except the primary key) is contained, needs to contain the names of the non primary key columns in the .csv. The second element in the tuple is an arbitrary weight assigned to each component of the scenario. Higher weights can be assigned to elements that are more relevant or they can all be of the same value.

It is recommended to use the optional sorting scheme, with just random shuffling workers might get unevenly distributed and repetitive scenarios. After making the optional changes the script can be run, it requires 5 arguments:
- .csv file name (e.g. scenarios.csv)
- unique study identifier (e.g. *studyname*)
- number of batches, calculated as total scenarios divided by batch size (e.g. 72)
- number of repetions, how many times does each scenario need to be completed (e.g. 5)
- sorting scheme, 1 if enabled (*item_weights* needs setting), 0 if disabled (e.g. 1)

Using the example arguments the script can be run as:

```bash
python randomize_batches.py scenarios.csv studyname 72 5 1
```

##### 5.  Completion code
For this step the study needs to be set up on Prolific, so wait for that first. When it is set up on Prolific, add completion code for the study to the *completion_codes* table, easiest to do manually. Go to AWS DynamoDB insert new entry with the unique study identifier (e.g. *studyname*) and corresponding completion code in the *completion_codes* table.

##### 6. AWS DynamoDB pricing
A thing to watch out for is the free tier limits on DynamoDB, 25 WCUs and 25 RCUs of provisioned capacity. With 5 Tables at 5 Read and 5 Write Units each it's fine. When setting up a new project either change the capacity so that the sum of the Read/Write capacities of all tables is 25, or delete the tables of the old project (except for  *completion_codes*).

### Front-end HTML

After setting up the tables, next step is the front-end. The most important things is to keep the names consistent, an element needs to have the same name in the databases, html id tag and in *input_data.js*/*output_data.js*. For example "Field1" needs to be called "Field1" in the Scenarios_DB, the HMTL element which displays it's value needs to have "Field1" as the id tag, and in *input_data.js* the JSON object needs to have a variable called "Field1" with a type.

##### 1. Modify *index.html*

The only thing that needs to be changed here is *const studyname* on line 21 by changing it to the appropriate value, for example *studyname*. The value is saved in session storage so it doesn't need to be set anymore, and everything else can stay as is. In this way the back-end will know that this front-end code belongs to *studyname*.

##### 2. Modify *input_data.js* and *output_data.js*  

*input_data.js* and *output_data.js* contain two JSON objects, which contain the different scenario elements to be displayed and the worker responses. <br> In *input_data.js* add the database field name as name, and as type text or image (text for elements whose content is contained in innerHTML attribute and image for images that are uploaded somewhere with the specified url). <br> In *output_data.js* define the outputs, name should be the database field name and type can be text or anything else (text if the content is in the innerHTML attribute, anything else if the content is in the value attribute). <br>
It is enough to define what the inputs and outputs are, the web-app does the rest. An important thing is that the html elements that correspond to them need to have the id field set to the same name.

##### 3. Modify home.html

It needs to be modified in order to show the specific scenario format from the new project.

- Change the title on line 6
- Change the css style to fit the new project
- Change the body to fit the new project, keep in mind that id attributes of the input and output elements need to be the same as their DB names.

##### 4. Upload web-app front-end to AWS Amplify Console

Simplest way to do it is by putting all the html,css,js files in a directory and compressing it to a .zip file. Change the name of the .zip file to **index.zip**. Now go to AWS Amplify Console and follow these steps:
- Click "connect app" which will lead to the "Host your web app" screen
- Select the "Deploy without Git provider" radio button and click "continue"
- Give the app and environment a name (they can be anything)
- Drag and drop the **index.zip** file or click "Choose files" and add it
- Then click "Save and deploy"
- Wait for the web-app to deploy and it's done

### Prolific study

Create a new study on Prolific and add the following things:

- Under "STUDY LINK" check the radio button "I'll use URL parameters", now in the "What is the URL of your study?" it shows "?PROLIFIC_PID={{%PROLIFIC_PID%}}&STUDY_ID={{%STUDY_ID%}}&SESSION_ID={{%SESSION_ID%}}".
- Add the URL of the web-app to the beginning of the textbox. The URL can be found at the AWS Amplify Console, let's suppose this is the web-app URL https://exampleurl.com, so the link to add to the textbox should look like this "https://exampleurl.com?PROLIFIC_PID={{%PROLIFIC_PID%}}&STUDY_ID={{%STUDY_ID%}}&SESSION_ID={{%SESSION_ID%}}"
- Under "STUDY COMPLETION" check the "I'll redirect them using a URL" radio button, now it will show the URL with the completion code  (e.g. https://app.prolific.co/submissions/complete?cc=12345678).
- Take only the completion code (e.g. 12345678) and add it to the *completion_codes* table, check end of the Database Tables section of this README.
- Try the preview and see if the web-app is behaving properly
