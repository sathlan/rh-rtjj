=============================
 rtjj - Run That Jenkins Job
=============================

Description
===========

This tool help:
 - discover available jobs based on named regex;
 - run a job based on cli argument or configuration file;
 - run multiple jobs;
 - check the status of the jobs run;

The basic workflow would be:
 - create a file with the parameters you need for your testing;
 - run one or multiple jobs with those parameters;
 - output the result in a csv format;
 - consume the previous output to check status of those jobs;
 - send notification;
