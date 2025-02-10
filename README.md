# Binance Asset Notifier with AWS Lambda & Terraform

This project is an **AWS Lambda function** that retrieves personal asset data from the **Binance API** and sends it to a
**Telegram bot** every 5 minutes.
The deployment is managed using **Terraform**.

## 🛠️ Setup & Deployment

### 1. Prepare layer (requests)

```sh
pip install requests -t ./python
zip -r requests_layer.zip ./python
```

### 2. Create environment variables

API_KEY= `binance api key`
API_SECRET= `binance api secret`
BOT_TOKEN= `telegram bot api key`
CHATS_LIST= `(comma separated ids)`

### 3. Initialize & Apply Terraform

```sh
terraform init
terraform validate
terraform apply
```

### 4. Destroy Terraform

```sh
terraform destroy
```
