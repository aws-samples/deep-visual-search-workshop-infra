
# Welcome to Deep Visual Search CDK project!

This provisions all the required infra in your account for the [Deep Visual Search Lab](https://github.com/aws-samples/deep-visual-search-workshop-infra) using CDK.

**Note: If you're using an AWS provided event engine account, you can skip this as this module will automatically be pre-provisioned in your account.**

Please follow along if you're doing the lab in your own account.

Services it will deploy in your account:
1. Amazon SageMaker Studio and create a new user called MLEngineer
2. Amazon OpenSearch Service cluster for storing and searching image features
3. Amazon S3 buckets for training data and hosting the website
4. Amazon API Gateway + AWS Lambda for Website APIs
6. Setup IAM roles and permissions

The `cdk.json` file tells the CDK Toolkit how to execute your app.

This project is set up like a standard Python project.  The initialization
process also creates a virtualenv within this project, stored under the `.venv`
directory.  To create the virtualenv it assumes that there is a `python3`
(or `python` for Windows) executable in your path with access to the `venv`
package. If for any reason the automatic creation of the virtualenv fails,
you can create the virtualenv manually.

To manually create a virtualenv on MacOS and Linux:

```
$ python3 -m venv .venv
```

After the init process completes and the virtualenv is created, you can use the following
step to activate your virtualenv.

```
$ source .venv/bin/activate
```

If you are a Windows platform, you would activate the virtualenv like this:

```
% .venv\Scripts\activate.bat
```

Once the virtualenv is activated, you can install the required dependencies.

```
$ pip install -r requirements.txt
```

We will need your aws account id and deployment region as environment variables.

```
$ export ACCOUNT={Your aws account id}
$ export REGION={Your aws region}
```

This setup will need CDK CLI, docker & NodeJS 16.x to be installed. If you don't have it installed, please follow the links to install it:
* [Docker](https://docs.docker.com/engine/install/)
* [CDK](https://docs.aws.amazon.com/cdk/v2/guide/getting_started.html#getting_started_install)
* [Node](https://nodejs.org/en/download/)

Create a directory for frontend code to build

```
$ mkdir ./frontend/build
```

If you're using cdk for the first time in your account, please run:

```
$ ./cdk-bootstrap-to.sh $ACCOUNT $REGION
```

At this point you can now synthesize the CloudFormation template for this code.

```
$ ./cdk-synth-to.sh $ACCOUNT $REGION
```

The next set of commands will deploy your infrastructure to your AWS account

```
$ ./cdk-deploy-to.sh $ACCOUNT $REGION VisualSearchEngineInfraStack --outputs-file ./frontend/src/config/config.json
$ cd frontend
$ npm install
$ npm run-script build
$ cd ..
./cdk-deploy-to.sh $ACCOUNT $REGION VisualSearchEngineFrontendStack
```

Enjoy!

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.
