build:
	sam build

deploy-dev: build
	sam deploy

deploy-prod: build
	sam deploy \
		--stack-name weatherstation-prod \
		--s3-prefix weatherstation-prod \
		--parameter-overrides \
		ParameterKey=DeploymentStage,ParameterValue=Production \
		ParameterKey=ApiStageName,ParameterValue=prod