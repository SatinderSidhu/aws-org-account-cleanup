Welcome to AWS Account Management open source script. This script can help you to manage your AWS Accounts under AWS Organizations to do bulk operations i.e. Change OU, Change email address, Close etc. 

# AWS Organizations operations to manage multiple accounts 
This project provides help to manage multiple AWS Accounts under AWS Organizations to transfer to another entity, move to another OU or close the account. 
*  Change the root email ID of an AWS Account 
*  Move the OU ( Organization Unit) to another OU one with the same Org.
*  Close the AWS Account. 
*  Delete the SSO Account created in Identity Center


## Prerequisites

Before you start you should have the following prerequisites:
  * An Organization in AWS Organizations
  * Administrative access to the AWS IAM 
  * Python version 3.10.5 or later
  * AWS CLI
  * Boto3


## Install prerequisites

Install Python - Make sure you are on the latest version of python and boto
```
sudo yum update
sudo yum install -y python3-pip python3 python3-setuptools
```
Install Boto3
```
pip3 install boto3
```
Install AWS Cli
```
$ curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
```
Please make sure you have the following OU created on control tower
* archive
* external
* suspended

Once you have above OY created, update the OU Ids here [accountscleanup.py](/https://github.com/SatinderSidhu/aws-org-account-cleanup/blob/main/accountscleanup.py#L17)


## Environment Setup

Create an IAM User

Please go to [IAM](https://us-east-1.console.aws.amazon.com/iam)

Create a user an IAM user and create access keys and token 

Clone this repo:
```
git clone https://github.com/SatinderSidhu/aws-org-account-cleanup.git
```
Set up your access to to AWS Console
```
aws configure
```
Verify your access
```
aws sts get-called-identity
```


## Managing the AWS Accounts for Moving OU, Internal or External Transfer, Close account

### Supported operations
#### external-org-start
> This operation will start invitation to new email & change the OU to external 
#### external-org-finish
> This operation will remove the AWS Account from Org
#### internal
> This operation will start invitation to new email & change the OU to provided one
#### close
> This operation will initiate to close the account
#### archive
> This operation will move the OU to archive



You can download the sample [CSV file](/accountscleanup-sample.csv) and keep it in the same folder as code. Update the information into new file called accountscleanup.csv


Here is an example to see all supported operations available in the sample script.

```
python3 accountscleanup.py cleanup  --filename accountscleanup.csv
```


## Deleting all SSO Accounts 

You can download the sample [CSV file](/delete-sso-accounts-sample.csv) and keep it in the same folder as code. Update the information into new file called delete-sso-accounts.csv


Here is an example to see all supported operations available in the sample script.

```
python3 delete-sso-accounts.py delete_sso_accounts_bulk  --filename delete-sso-accounts.csv
```

## Deleting all resources in AWS Accounts

if you are considering deleting all the resources within an AWS account consider this [aws nuke](https://github.com/rebuy-de/aws-nuke)
```
https://github.com/rebuy-de/aws-nuke
```

## Renaming the AWS Account

Renaming of AWS Account is yet not supported  by AWS API, please follow the following guide to rename the AWS Account 
```
[https://github.com/rebuy-de/aws-nuke](https://docs.aws.amazon.com/controltower/latest/userguide/change-account-name.html)
```



## License

This library is licensed under the MIT-0 License. See the LICENSE file. Please verify this script before running in your production environment, We are not responsible for any damages

