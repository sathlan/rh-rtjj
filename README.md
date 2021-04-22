# rtjj - run that jenkins job #

## Description ##

This tool can:

 - list available jobs: `rtjj-list`
 - create builds: `rtjj-create`
 - check the status of builds: `rtjj-check`

## Examples ##

### Trigger a bunch of jobs with specifics parameters ### 

I need to test a patch that implement a better update functionality on
several jobs named Test-v1, Test-v2, Test-v8. I can pass a PATCH
parameter to the parametrized jenkins job that would point to an
available file.

1. Collect the jobs name:

        rtjj-list --server https://myJenkins.com --pattern 'Test-v[128]' --named 'Better-update' > ~/.config/jenkins/conf.ini

2. Add the parameter to the job
   
        echo 'PATCH = https://file_server/patch1' >> ~/.config/jenkins/conf.ini

3. Configure the server, and add the TIMEOUT parameter to all jobs using that server.

        cat >> conf.ini
        [myJenkins.com]
        auth = ~/.config/jenkins/jenkins.auth
        server_url  = https://myjenkins.com/
        TIMEOUT = 3600

4. Create an API key on your jenkins server and add it to the auth file.

        echo 'myUser:myAPIKey' > ~/.config/jenkins/jenkins.auth
    
5. Run the build !

        rtjj-create --conf ~/.config/jenkins/conf.ini --jobs Better-update > test-better-update.csv
    
6. Without the configuration this would be:

        rtjj-create --job Test-v1 --job Test-v2 --job Test-v8 \
                --server https://myjenkins.com/ \
                --auth ~/.config/jenkins/jenkins.auth \
                --params TIMEOUT=3600 --params PATCH=https://file_server/patch1 \
                > test-better-update.csv

This would output a csv file looking like this:

    start,desc,url
    <date>,Better-update,https://myjenkins.com/Test-v1/8
    <date>,Better-update,https://myjenkins.com/Test-v2/7
    <date>,Better-update,https://myjenkins.com/Test-v8/9

Then `rtjj-check` can be used to consume that file and verify the
current status. The status will be output as a csv file.

    cat test-better-update.csv | rtjj-check 
    start,desc,url,status,failure_stage
    <date>,Better-update,https://myjenkins.com/Test-v1/8,RUNNING,
    <date>,Better-update,https://myjenkins.com/Test-v2/7,FAILED,stage1
    <date>,Better-update,https://myjenkins.com/Test-v8/9,SUCCESS,

### List the status history of jobs ###

I want to verify the status history of a list of jobs for further
analysis from an csv file.

    rtjj-list --server https://myJenkins.com --pattern 'Test-v[128]' --history > current_hist_status.csv
    
That file can again be consumed by `rtjj-check` if some jobs are still running.

### Get a notification when a job finish ###

    while true:
        if rtjj-check status.csv | grep RUNNING; then
            sleep 10
        else
            notify-send "Jobs ended"
            break
