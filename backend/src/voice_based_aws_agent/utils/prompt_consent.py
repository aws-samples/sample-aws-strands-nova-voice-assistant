"""
Prompt-based Consent System for AWS Operations
Works with existing Strands architecture and use_aws tool.
"""

# Define dangerous operations that require consent
DANGEROUS_AWS_OPERATIONS = {
    'ec2': [
        'terminate-instances',
        'stop-instances', 
        'reboot-instances',
        'delete-security-group',
        'delete-volume',
        'delete-snapshot',
        'delete-key-pair'
    ],
    'ssm': [
        'send-command',
        'delete-document',
        'delete-parameter',
        'put-parameter',
        'delete-patch-baseline',
        'delete-maintenance-window'
    ],
    'backup': [
        'delete-backup-vault',
        'delete-backup-plan',
        'delete-recovery-point',
        'stop-backup-job'
    ]
}

def get_consent_instructions() -> str:
    """
    Get prompt instructions for handling dangerous AWS operations.
    This is added to agent system prompts to enable consent checking.
    """
    return f"""
IMPORTANT SAFETY PROTOCOL FOR AWS OPERATIONS:

Before executing ANY of these dangerous AWS operations, you MUST ask for explicit user consent:

DANGEROUS EC2 OPERATIONS (require consent):
- terminate-instances (permanently destroys instances)
- stop-instances (shuts down instances)
- reboot-instances (restarts instances)
- delete-security-group (deletes security groups)
- delete-volume (deletes EBS volumes)
- delete-snapshot (deletes EBS snapshots)
- delete-key-pair (deletes SSH key pairs)

DANGEROUS SSM OPERATIONS (require consent):
- send-command (executes commands on instances)
- delete-document (deletes SSM documents)
- delete-parameter (deletes parameters)
- put-parameter (creates/modifies parameters)
- delete-patch-baseline (deletes patch baselines)
- delete-maintenance-window (deletes maintenance windows)

DANGEROUS BACKUP OPERATIONS (require consent):
- delete-backup-vault (deletes backup vaults and all recovery points)
- delete-backup-plan (deletes backup plans)
- delete-recovery-point (deletes individual recovery points)
- stop-backup-job (stops running backup jobs)

CONSENT PROTOCOL:
1. If user requests a dangerous operation, DO NOT call use_aws immediately
2. First explain what the operation will do and its potential impact
3. Ask for explicit consent: "Do you want me to proceed? Please say 'yes' to continue or 'no' to cancel."
4. Wait for user response
5. Only call use_aws if user explicitly approves (says "yes", "proceed", "continue", etc.)
6. If user declines or seems uncertain, do not execute the operation

SAFE OPERATIONS (no consent needed):
- describe-* (describe-instances, describe-volumes, etc.)
- list-* (list-backup-jobs, list-parameters, etc.)
- get-* (get-parameter, get-command-invocation, etc.)
- show-* operations
- status and health checks

EXAMPLE CONSENT FLOW:
User: "Terminate instance i-1234567890abcdef0"
Agent: "I can terminate EC2 instance i-1234567890abcdef0 for you. This will permanently destroy the instance and all data stored on it. This action cannot be undone. Do you want me to proceed? Please say 'yes' to continue or 'no' to cancel."
User: "yes"
Agent: "Understood. Terminating the instance now..." [then calls use_aws]

EXAMPLE DENIAL:
User: "Delete all my backup vaults"
Agent: "I can delete your backup vaults, but this will permanently remove all backup vaults and their recovery points. All backup data will be lost and cannot be recovered. Do you want me to proceed? Please say 'yes' to continue or 'no' to cancel."
User: "no"
Agent: "Operation cancelled. Your backup vaults will not be deleted."

Remember: ALWAYS ask for consent before dangerous operations. NEVER assume the user wants to proceed with destructive actions.
"""

def is_dangerous_operation(service: str, operation: str) -> bool:
    """
    Check if an AWS operation is dangerous and requires consent.
    
    Args:
        service: AWS service name (e.g., 'ec2', 'ssm', 'backup')
        operation: AWS operation name (e.g., 'terminate-instances')
        
    Returns:
        True if operation requires consent, False otherwise
    """
    service_lower = service.lower()
    operation_lower = operation.lower()
    
    dangerous_ops = DANGEROUS_AWS_OPERATIONS.get(service_lower, [])
    return operation_lower in dangerous_ops
