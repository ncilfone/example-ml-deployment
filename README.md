CI/CD Process (use]ing something like Jenkins, Github actions, etc.)

Builds docker image
Checks to see if ECR exists if not create
Pushes image to ECR
Runs cdktf synth
Runs cdktf deploy
Runs cdktf outputs (to get endpoint outputs to json)

Runs separate APIGW cdtf stuff to link SM endpoint to API GW (not shown here)

Git pushes generated TF back into repository for lineage and stateful IaaC