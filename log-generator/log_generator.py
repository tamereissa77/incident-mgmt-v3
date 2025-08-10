print("--- THIS IS THE LATEST VERSION OF THE SCRIPT ---")
import random
import uuid
from datetime import datetime, timezone
from time import sleep
from faker import Faker
from confluent_kafka import Producer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.json_schema import JSONSerializer
from confluent_kafka.serialization import SerializationContext, MessageField

# --- Configuration ---
NUM_LOG_LINES = 1000000
fake = Faker('en')

# --- Data Pools for Realism ---
USER_IDS = [f"user_{i:06d}" for i in range(1, 10001)]  # 10000 unique users
SYSTEM_IDS = [f"SYS-{i:04d}" for i in range(1, 501)]  # 500 systems
SERVICE_NAMES = [
    "web-server", "database", "api-gateway", "auth-service", "payment-service",
    "email-service", "file-storage", "cache-redis", "load-balancer", "monitoring",
    "backup-service", "cdn", "message-queue", "search-engine", "analytics"
]
SEVERITY_LEVELS = ["Critical", "High", "Medium", "Low"]
INCIDENT_CATEGORIES = [
    "Hardware Failure", "Software Bug", "Network Issue", "Security Breach",
    "Performance Degradation", "Service Outage", "Data Corruption", "Configuration Error"
]

# --- IT Incident Event Templates ---
# Incident Events (INFO for resolved, WARNING for ongoing, ERROR for critical)
INCIDENT_EVENTS_INFO = [
    {"action": "incident_resolved", "level": "INFO", "message_template": "Incident {incident_id} resolved. Service: {service}. Duration: {duration} minutes. Affected users: {affected_users}. Resolved by: {resolver}"},
    {"action": "system_recovered", "level": "INFO", "message_template": "System {system_id} recovered from {category}. Service: {service}. Recovery time: {duration} minutes. Status: Operational"},
    {"action": "maintenance_completed", "level": "INFO", "message_template": "Scheduled maintenance completed for {service}. System: {system_id}. Duration: {duration} minutes. No issues detected"},
]

INCIDENT_EVENTS_WARNING = [
    {"action": "incident_detected", "level": "WARNING", "message_template": "Incident {incident_id} detected. Service: {service}. Category: {category}. Severity: {severity}. Affected users: {affected_users}. Assigned to: {assignee}"},
    {"action": "performance_degradation", "level": "WARNING", "message_template": "Performance degradation detected on {service}. System: {system_id}. Response time increased by {performance_impact}%. Investigating..."},
    {"action": "resource_threshold", "level": "WARNING", "message_template": "Resource threshold exceeded on {system_id}. Service: {service}. CPU: {cpu_usage}%, Memory: {memory_usage}%, Disk: {disk_usage}%"},
]

INCIDENT_EVENTS_ERROR = [
    {"action": "critical_incident", "level": "ERROR", "message_template": "CRITICAL incident {incident_id}. Service: {service} DOWN. Category: {category}. Affected users: {affected_users}. Escalated to: {escalation_team}"},
    {"action": "security_breach", "level": "ERROR", "message_template": "SECURITY BREACH detected. Incident: {incident_id}. System: {system_id}. Attack type: {attack_type}. Source IP: {source_ip}. Immediate action required"},
    {"action": "data_corruption", "level": "ERROR", "message_template": "DATA CORRUPTION detected. Incident: {incident_id}. System: {system_id}. Database: {database}. Records affected: {affected_records}. Backup restoration initiated"},
]

# Additional data pools for IT incidents
ATTACK_TYPES = ["SQL Injection", "DDoS", "Malware", "Phishing", "Brute Force", "Cross-Site Scripting", "Man-in-the-Middle"]
ESCALATION_TEAMS = ["L2-Support", "DevOps", "Security-Team", "Database-Admin", "Network-Team", "Infrastructure"]
RESOLVERS = ["john.doe", "jane.smith", "mike.wilson", "sarah.johnson", "alex.brown", "lisa.davis"]
ASSIGNEES = ["support.team", "ops.team", "dev.team", "security.team", "network.team"]
DATABASES = ["user_db", "product_db", "analytics_db", "logs_db", "config_db", "backup_db"]

JSON_SCHEMA_STR = """
{
    "title": "ITIncidentEvent",
    "description": "An IT incident log event message",
    "type": "object",
    "properties": {
        "timestamp": {
            "description": "The ISO 8601 timestamp of the incident event",
            "type": "string"
        },
        "level": {
            "description": "The log level (INFO, WARNING, ERROR)",
            "type": "string"
        },
        "message": {
            "description": "The incident log message content",
            "type": "string"
        }
    },
    "required": ["timestamp", "level", "message"]
}
"""

def generate_log_entry(current_time):
    level = "INFO"
    message_parts = {}  # Initialize an empty dictionary

    # Randomly choose between different incident severity levels
    event_list = random.choices(
        [INCIDENT_EVENTS_INFO, INCIDENT_EVENTS_WARNING, INCIDENT_EVENTS_ERROR],
        weights=[0.6, 0.3, 0.1],  # 60% resolved, 30% warnings, 10% critical
        k=1
    )[0]

    # Randomly select an event specification from the chosen list
    event_spec = random.choice(event_list)

    # Extract the level from the event specification
    level = event_spec["level"]

    # Generate realistic data for the incident
    message_parts = {
        "incident_id": f"INC-{uuid.uuid4().hex[:8].upper()}",
        "system_id": random.choice(SYSTEM_IDS),
        "service": random.choice(SERVICE_NAMES),
        "category": random.choice(INCIDENT_CATEGORIES),
        "severity": random.choice(SEVERITY_LEVELS),
        "affected_users": random.randint(1, 5000),
        "duration": random.randint(5, 480),  # 5 minutes to 8 hours
        "resolver": random.choice(RESOLVERS),
        "assignee": random.choice(ASSIGNEES),
        "escalation_team": random.choice(ESCALATION_TEAMS),
        "performance_impact": random.randint(10, 200),
        "cpu_usage": random.randint(70, 100),
        "memory_usage": random.randint(75, 95),
        "disk_usage": random.randint(80, 98),
        "attack_type": random.choice(ATTACK_TYPES),
        "source_ip": fake.ipv4_public(),
        "database": random.choice(DATABASES),
        "affected_records": random.randint(100, 100000)
    }

    # .format will only use keys present in the template string
    message = event_spec["message_template"].format(**message_parts)
    key = event_spec["action"]

    # Create the log entry dictionary
    # Use ISO 8601 format for the timestamp
    return {
        "timestamp": current_time.isoformat(),
        "level": level,
        "message": message
    }, key


if __name__ == "__main__":

    # --- Schema Registry Client Configuration ---
    schema_registry_conf = {'url': 'http://schema-registry:8081'}
    schema_registry_client = SchemaRegistryClient(schema_registry_conf)

    # --- JSON Serializer for the message value ---
    # The JSONSerializer will automatically register the JSON schema with Schema Registry
    json_serializer = JSONSerializer(
        JSON_SCHEMA_STR,
        schema_registry_client
    )

    # --- Kafka Producer Configuration ---
    producer_conf = {
        'bootstrap.servers': 'kafka1:29092',
        'client.id': 'IT-Incident-Management-System'
    }

    # Create a Kafka producer instance
    try:
        producer = Producer(producer_conf)
        print("IT Incident Producer created successfully.")
    except Exception as e:
        print(f"Failed to create producer: {e}")
        exit(1)

    try:
        print("Starting IT incident log generation...")
        counter = 1

        # Start generating logs indefinitely
        while True:
            try:
                producer.poll(0)

                current_log_time = datetime.now(timezone.utc)
                log_entry, key = generate_log_entry(current_log_time)

        # The actual sending of the message
                producer.produce(topic="incidents",
                                key=key,
                                value=json_serializer(log_entry, SerializationContext("incidents", MessageField.VALUE))
                                )
        
        # This part only runs if the produce call was successful
                if counter % 100 == 0:
                    print(f"Generated {counter} IT incident entries...")
                counter += 1

            except BufferError:
        # This is a common Kafka error when the producer queue is full
                print("WARN: Kafka producer queue is full. Polling...")
                producer.poll(1) # Poll for a full second to clear the buffer

            except Exception as e:
        # Catch any other unexpected errors
                print(f"ERROR: An exception occurred in the main loop: {e}")
                print("WARN: Waiting 10 seconds before retrying...")
                sleep(10)

    # Sleep outside the try block to ensure it always happens
            sleep(random.uniform(1, 5))

    finally:
        print("Flushing producer...")
        # Flush the producer to ensure all messages are sent
        producer.flush(30)
        print("Producer flushed and closed.")