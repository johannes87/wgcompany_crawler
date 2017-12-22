A web crawler that crawls wgcompany.de and sends you a mail for each new
flatshare.

# Setup

1. Copy crawler.cfg.example to crawler.cfg
2. Replace the example values in crawler.cfg with your actual configuration
3. Install 'pipenv' if not already installed
4. Run `pipenv install`
5. Run `pipenv shell`
6. Test your configuration: Run `python test_crawler.py`. 

It should print "OK" and you should have received two test mails to the account you configured in step 2

7. Run the crawler the first time: `./crawler.py`

Nothing should be printed on the console. Log files will be in `crawler.log`.
You won't receive any mails on the first run.

8. Look at the path that was output when running `pipenv shell` in step 4. 

The path looks like this: `/Users/YOURNAME/YOUR_ACTUAL_PATH/bin/activate`
Replace `activate` with `python` and note that path for later.
So you get something like this: `/Users/YOURNAME/YOUR_ACTUAL_PATH/bin/python`


9. Create a crontab entry which runs the crawler periodically

- Run `crontab -e`
- Put the following line in the crontab and save the file

`0 * * * * /Users/YOURNAME/YOUR_ACTUAL_PATH/bin/python PATH_TO_crawler.py`

# That's it

The above setup will run the crawler once an hour.


