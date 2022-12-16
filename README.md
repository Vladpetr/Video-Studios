# Fake-Video-Studios
Cloud architecture for a website where people can log on, upload a photo of a character, and a long script. The website then takes about 15 minutes to generate a short video in which that character acts out the script.

## Structure
AWS CloudFormation template: *cloud architecture.yaml*

The application is not yet finished. However, it currently contains a few webpages where the user can sign up or log in and access the home page. During the authentication, the user credentials are saved (or checked against) an RDS MySQL database. The goal is to place the application on the EC2 instance that acts as a server. The cloud infrastructure is already configured.
