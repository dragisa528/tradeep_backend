r### TASKS

- [ ] **1. User Configurations and JSON Generation (Frontend):**
    This task isn't directly related to the backend, but it's a prerequisite for the following backend tasks.

- [ ] **2. Setup Django GraphQL API (Backend):**
    This API will receive the JSON from the frontend and trigger the task queue.
    - [ ] 2.1. Create a new Django app (e.g., `training_api`).
    - [ ] 2.2. Within this app, create a new file (e.g., `schema.py`) and define a new GraphQL mutation (e.g., `TrainMutation`).
    - [ ] 2.3. Parse the incoming JSON, validate the data, and create a task in the queue.

- [ ] **3. Setup Task Queue System (Infrastructure):**
    The Django API will push training tasks to this queue, and the worker nodes will pull tasks from it.
    - [ ] 3.1. Setup AWS SQS and create a new queue (e.g., `training-queue`).
    - [ ] 3.2. In your Django app, add logic to push tasks to this queue (e.g., in `schema.py`).

- [ ] **4. Setup Worker Nodes (Infrastructure & Backend):**
    The worker nodes will pull tasks from the queue, execute the Python snippets, and initiate model training.
    - [ ] 4.1. Setup AWS EC2 instances and configure them as worker nodes.
    - [ ] 4.2. On the worker nodes, create a new script file (e.g., `worker.py`). This script will pull tasks from the queue, execute Python snippets, initiate model training, and read/write data from/to PyStore.

- [ ] **5. Data Acquisition and PyStore Integration (Backend):**
    This involves setting up data fetching and updating, and storing the data using PyStore.
    - [ ] 5.1. Identify the data sources.
    - [ ] 5.2. Write a script (e.g., `data_acquisition.py`) that fetches and updates data. Use OpenBB SDK for data acquisition, if applicable.
    - [ ] 5.3. Store the fetched data in PyStore in an efficient partitioned manner.

- [ ] **6. Setup AWS Glue (Infrastructure):**
    This will catalog your data on S3.
    - [ ] 6.1. Setup AWS Glue and configure it to crawl your data on S3.
    - [ ] 6.2. Ensure your Glue Data Catalog is accessible from your worker nodes.

- [ ] **7. User-Specific Data Handling (Backend):**
    This involves applying user-specific transformations to the data before training.
    - [ ] 7.1. In your Django app, add logic to store user-specific Python snippets (maybe in `models.py`).
    - [ ] 7.2. In your worker node script (`worker.py`), add logic to fetch and apply these transformations.

- [ ] **8. Training Results Storage (Infrastructure & Backend):**
    This involves saving the training results and weights to S3.
    - [ ] 8.1. In your worker node script (`worker.py`), add logic to save the results and weights to a specific S3 bucket.
    - [ ] 8.2. Setup S3 buckets for storing results and configure proper permissions.

- [ ] **9. Setup PostgreSQL Database (Infrastructure & Backend):**
    This involves storing user information, model configurations, and training sessions' metadata.
    - [ ] 9.1. Setup a PostgreSQL database instance.
    - [ ] 9.2. In your Django app, add logic to connect to this database and perform CRUD operations.

- [ ] **10. Cost Management (Infrastructure):**
    This involves setting up autoscaling, using a mix of on-demand and spot instances, and regularly cleaning up old S3 objects.
    - [ ] 10.1. Configure autoscaling rules for your EC2 instances.
    - [ ] 10.2. Setup a mix of on-demand and spot instances.
    - [ ] 10.3. Write a script (e.g., `cleanup.py`) that regularly reviews and deletes old S3 objects.



# Stack django-backend-postgresql
django
graphql
aws
s3
spot instance OR ec2

### backend :
- each user can build model
- each user can set training config, select features and data.
- each user can train ,
- each user can backtest
- each user can add account

### CMS
- Admin can see dashbaord stat
- user table + search
- monitor payments
- Add content


### frameworks:
- pystore 
- quantstats
- openBB sdk 
- LMAX api https://docs.lmax.com/ 
- mtsim
- mlflow for tracking 
- pytrader for brokers.
- finrl 

### Backend Integration:
-  freqtrade integration
-  migration from fastapi to django
-  adding strategies

## TASKS





