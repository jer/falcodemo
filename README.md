# falcodemo
This is a demo of using Falco in Kubernetes

To try it out, first put your Telegram bot token in a file, e.g. `token`.
Then make a Kubernetes secret out of it:

    kubectl create secret generic bot-api-token --from-file=./token

Now deploy all the things and wait:

    kubectl apply -f ./

If everything starts without trouble, you should be able to subscribe to Falco
priorities by sending a command like this to your bot:

    /subscribe Critical
