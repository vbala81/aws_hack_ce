ps -ef | grep '[c]ircular' | awk '{print $2}' | xargs kill -9 
