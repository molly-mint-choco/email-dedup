# Email Deduplication System

A high-performance scalable email deduplication system that identifies duplicate and near-duplicate email threads using similarity hashing. The system processes email documents, detects thread hierarchies, and exposes a REST API for querying canonical threads.

## Features

- **Near-Duplicate Detection**: Uses SimHash algorithm to identify duplicate and near-duplicate emails with configurable bit distance threshold
- **Thread Hierarchy Tracking**: Automatically identifies parent-child relationships in email threads
- **Async Architecture**: Built with FastAPI and async/await for high-performance processing
- **Kafka Integration**: Producer-consumer pattern for scalable email ingestion
- **REST API**: Query canonical threads, document mappings, and thread hierarchies
- **Code-First MySQL Storage**: Uses code-first approach to initialize database with SQLAlchemy ORM

## Architecture

The system follows clean architecture principles with distinct layers:

```
src/
├── app/
│   ├── api/          # REST API routes
│   ├── application/  # Business logic
│   ├── domain/       # Data models
│   ├── infrastructure/  # Database and repository implementations
│   └── services/     # Kafka producer/consumer services
├── config.py         # Configuration loader
├── settings.toml     # Configuration file
└── main.py          # Application entry point
```

## ❗❗<mark><span style="color:red">Assumptions</span></mark>❗❗

### Emails and Thread Relations

- All emails come in chronological order. 
- Parent emails come in before child emails.
- Assume deduplication is performed on a parent email before any of its child emails arrive. As a result, scenarios like 0-1m-2 will not occur, since a near-duplicate parent (0-1m) would already have been removed before the next canonical thread is generated.
- The first email received in the canonical thread is considered the baseline. Any emails belonging to the same canonical thread that arrive after the baseline and are duplicates or near-duplicates are labeled accordingly. For example, the first email is labeled 0-1; a near-duplicate arriving after 0-1 is labeled 0-1m. A near-duplicate email (0-1m) cannot logically arrive before the original baseline email (0-1). Duplicate emails will be removed (but will still be saved in the Document table in the database).
- A parent email can have multiple child emails, e.g., 0-1 (P), 0-1-2 (C1), 0-1-3 (C2). 
- A child email can have only one parent; i.e., the canonical thread relations are traceable upwards only.
- The canonical thread hierarchy follows a tree structure.

### Content Parsing

- Replies appear on top of the previous emails in a single document.
- Replies are separated by a predefined divider. Assume it’s ‘-----Original Message-----’
- We’re not considering sender, recipient, topic, subject, datetime, etc., information as identifiers to separate replies and distinguish emails. 

### Data Ingestion

* To simulate the sequential arrival of emails in real life, files are read from the data folder in order of their creation time and processed through a data ingestion pipeline using a message queue.

## How It Works

1. **Email Ingestion**: Producer service reads email files and publishes to Kafka
2. **Email Processing**: Consumer service processes emails:
   - Computes SimHash for the entire email content
   - Splits emails into parts using predefined delimiter
   - Checks for near-duplicates against existing canonical threads
   - Creates new canonical thread or links to existing duplicate
   - Identifies parent threads by hashing email content minus most recent part
3. **API Queries**: REST API provides access to thread relationships and document mappings

## Prerequisites

- Python 3.13+
- MySQL 5.7+ or 8.0+
- Apache Kafka (for distributed processing)
- Docker (for kubernetes deployment)

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd email-dedup
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure the system**
   
   Edit `src/settings.toml` with your configuration:
   ```toml
   [database]
   username = "your_db_user"
   password = "your_db_password"
   host = "localhost"
   port = 3306
   database_name = "email_dedup"
   
   [kafka]
   bootstrap_servers = "localhost:9092"
   topic = "email-ingest"
   
   [email]
   read_dir = "data/eval"
   max_workers = 4
   threshold = 10  # SimHash bit distance threshold
   ```

4. **Set up the database**
   
   The application will automatically create tables on first run.

## Usage

### Running with Kubernetes

Set up kafka service for kubernetes, then run the following command.

```bash
docker build -t email-dedup:latest .
kubectl apply -n email-dedup -f deployment.yaml
kubectl rollout status -n email-dedup deploy/email-dedup-app
```

### Running Locally

```bash
python src/main.py
```

This starts three concurrent services:
- **REST API**: 
  - local: http://localhost:8000/docs
  - k8s: http://localhost:30080/docs
- **Kafka Producer**: Ingests emails from configured directory
- **Kafka Consumer**: Processes emails and stores results

### API Endpoints

#### Get Canonical ID by Document
```http
GET /emails/document/{file_name}/canonical-id
```
Returns the canonical thread ID for a given document.

#### Get Documents by Canonical Thread
```http
GET /emails/canonical-thread/{cano_id}/documents
```
Returns all document filenames associated with a canonical thread.

#### Get Child Threads
```http
GET /emails/canonical-thread/{cano_id}/children
```
Returns all child thread IDs for a given canonical thread.

#### Get Parent Thread
```http
GET /emails/canonical-thread/{cano_id}/parent
```
Returns the parent thread ID for a given canonical thread.

#### Get Hierarchy Chain
```http
GET /emails/canonical-thread/{cano_id}/upstream
```
Returns the complete upstream hierarchy chain for a canonical thread.

## Configuration

### Application

Key configuration parameters in `settings.toml`:

| Parameter | Description | Default |
|-----------|-------------|---------|
| `email.threshold` | SimHash bit distance threshold for duplicate detection | 10 |
| `email.max_workers` | Thread pool size for hash computation | 4 |
| `kafka.consumer.max_workers` | Concurrent Kafka consumer workers | 2 |
| `kafka.consumer.poll_interval` | Kafka polling interval (seconds) | 1.0 |
| `kafka.consumer.min_commit_count` | Decide consumer commit frequency | 1 |

### Kubernetes Deployment

Key configuration parameters in `deployment.yaml`:

| Config | Description |
|------|-------------|
| `initContainers.wait-for-kafka` | Blocks application startup until Kafka is reachable |
| `APP_ENV` | Distinguishes runtime environment (local vs container) |
| `KAFKA_SERVERS` | Kafka bootstrap address |
| `KAFKA_SECURITY_PROTOCOL` | SASL authentication protocol |
| `KAFKA_SASL_MECHANISM` | SCRAM authentication mechanism |
| `KAFKA_SASL_USERNAME` | Kafka client identity |
| `KAFKA_SASL_PASSWORD` | Retrieved securely from a Kubernetes Secret |

## Data Model

### CanonicalThread
Represents a unique email thread:
- `id`: UUID primary key
- `parent_id`: Self-referencing foreign key for thread hierarchy
- `hash`: 64-bit SimHash value
- `parent_hash`: Hash of parent thread content
- `thread_length`: Number of emails in thread

### Document
Represents an email document:
- `id`: UUID primary key
- `file_name`: Original filename
- `cano_id`: Foreign key to CanonicalThread
- `email_metadata`: Raw email content

### AuditLog
Tracks all system operations for auditability.

## Development

### Project Structure
The project follows Domain-Driven Design (DDD) principles with clear separation of concerns:
- **Domain Layer**: Core business entities and logic
- **Application Layer**: Use cases and business workflows
- **Infrastructure Layer**: External services (database)
- **API Layer**: HTTP interface

### Testing
Simple functional test files are located in the respective service directories and include:
- `test_run_db.py`: Database connection tests
- `test_run_pub.py`: Kafka producer tests
- `test_run_sub.py`: Kafka consumer tests

## Dependencies

Key libraries used:
- **FastAPI**: Modern web framework for building APIs
- **SQLAlchemy 2.0+**: SQL toolkit and ORM
- **aiomysql**: Async MySQL driver
- **confluent-kafka**: Kafka client
- **simhash**: Similarity hashing implementation
- **loguru**: Simplified logging
- **pydantic**: Data validation

See [requirements.txt](requirements.txt) for complete list.

## Performance Considerations

- **Producer/Consumer Design**: Use an event-driven approach to improve scalability for potential heavy workloads, decoupling components.
- **Batch Processing**: Uses thread pool for parallel hash computation
- **Database Optimization**: Indexes on hash, thread_length, and foreign keys
- **Length-based Filtering**: Pre-filters candidates by thread length before computing hash distance
- **Async I/O**: Non-blocking file and database operations
- **Domain Driven Design**: Adopt domain driven design to keep solution modular, resilient and adaptable

## Improvement Features
- Use Redis to maintain a canonical thread pool containing only validated threads, avoid repeated database queries each time for SimHash comparisons.