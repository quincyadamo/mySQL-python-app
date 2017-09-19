# Python + MySQL Sample App

Description:
This is a wall/forum app using Python and SQL where users are able to post a message and see the message displayed by other users. This app includes login and registration. Authenticated users are able to post comments for any message created by other users.

![Example Image](https://s3.us-east-2.amazonaws.com/qadamo-images/wireframe-wall.png "Example Image")


## Installation & Activation:

### 1. virtualenv 
Simply create and activiate a virtual environment to run this project. In the Terminal, run: 
`$ virtualenv venv` (to create)
`$ source venv/bin/activate` (to activate)

### 2. MySql
Make sure MySql is running on your system on the same port specified in mysqlconnection.py and use wall.sql to create the necessary tables. 

### 4. Ready to activate the project? Go!
From the Terminal, run: 
`$ python server.py runserver`
