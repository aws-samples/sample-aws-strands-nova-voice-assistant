# AWS Strands Nova Voice Assistant

A sophisticated voice-based AI assistant using AWS Strands for multi-agent collaboration to interact with AWS services. The system features real-time voice interaction through Amazon Nova Sonic and intelligent routing between specialized AWS agents.

## 🚀 Features

- **Voice Interface**: Real-time voice input/output using Amazon Nova Sonic
- **Multi-Agent Architecture**: Supervisor agent coordinates between specialized agents
- **AWS Service Integration**: Comprehensive support for EC2, SSM, and AWS Backup operations
- **Intelligent Routing**: Automatic query routing to appropriate specialized agents
- **Professional UI**: AWS Cloudscape Design components with chat bubbles and event display

## Authors and acknowledgment
We would like to thank the following contributors for their valuable input and work on this project _(sorted alphabetically)_:

• Aditya Ambati 

• Anand Krishna Varanasi 

• JAGDISH KOMAKULA 

• Dadi T.V.R.L.Phani Kumar

## 🏗️ Architecture

The system implements a simplified multi-agent architecture:

![Architecture Diagram](diagrams/strands-arch.svg)

### Core Components

1. **Supervisor Agent**: Routes queries to specialized AWS agents
2. **Specialized Agents**:
   - **EC2 Agent**: Instance management, status checks, and operations
   - **SSM Agent**: Systems Manager operations, command execution, patch management
   - **Backup Agent**: AWS Backup configuration, job monitoring, and management
3. **Voice Integration**: Amazon Nova Sonic for speech-to-text and text-to-speech
4. **WebSocket Server**: Real-time communication between frontend and backend

### Technology Stack

- **Backend**: Python 3.12+ with AWS Strands framework
- **Frontend**: React with AWS Cloudscape Design components
- **AI Models**: AWS Bedrock Claude 3 Haiku for all agents
- **Voice Processing**: Amazon Nova Sonic for audio I/O
- **Package Management**: Standard pip with requirements.txt

## 📁 Project Structure

```
aws-strands-nova-voice-assistant/
├── backend/                           # Backend Python application
│   ├── src/
│   │   └── voice_based_aws_agent/
│   │       ├── agents/                # Multi-agent system
│   │       │   ├── orchestrator.py    # Central agent coordinator
│   │       │   ├── supervisor_agent.py # Query routing agent
│   │       │   ├── ec2_agent.py       # EC2 operations specialist
│   │       │   ├── ssm_agent.py       # SSM operations specialist
│   │       │   └── backup_agent.py    # Backup operations specialist
│   │       ├── config/                # Configuration management
│   │       ├── utils/
│   │       │   ├── aws_auth.py        # AWS authentication
│   │       │   └── voice_integration/ # Nova Sonic integration
│   │       │       ├── server.py      # WebSocket server
│   │       │       ├── s2s_session_manager.py # Stream management
│   │       │       └── supervisor_agent_integration.py # Agent bridge
│   │       └── main.py                # Application entry point
│   └── tools/                         # Strands tools
│       └── supervisor_tool.py         # Supervisor agent tool integration
├── frontend/                          # React web interface
│   ├── src/
│   │   ├── components/                # React components
│   │   ├── helper/                    # Audio processing utilities
│   │   ├── App.js                     # Main React application
│   │   └── VoiceAgent.js              # Voice interface component
│   └── package.json                   # Node.js dependencies
├── requirements.txt                   # Python dependencies
├── run_backend.sh                     # Backend startup script
├── run_frontend.sh                    # Frontend startup script
└── README.md                          # This file
```

## 💰 Detailed Cost Breakdown

Running this voice-driven AWS assistant involves several AWS services with usage-based pricing. Here's a comprehensive breakdown for planning and budgeting:

### Amazon Nova Sonic (Speech-to-Speech)
- **Speech input tokens**: $0.0034 per 1K tokens
- **Speech output tokens**: $0.0136 per 1K tokens  
- **Text input tokens**: $0.00006 per 1K tokens
- **Text output tokens**: $0.00024 per 1K tokens

### AWS Bedrock Claude 3 Haiku
- **Input tokens**: $0.00025 per 1K tokens
- **Output tokens**: $0.00025 per 1K tokens

### Supporting AWS Services

**Amazon EC2 (for testing/demo instances)**
- **t3.micro Linux**: $0.0104 per hour (~$7.49/month if running 24/7)
- **Most users run instances only during testing**

**AWS Systems Manager**
- **Basic operations**: Free tier available
- **Advanced parameters**: $0.05 per parameter per month
- **Data transfer**: $0.90 per GB (rarely needed for typical usage)

**AWS Backup**
- **Storage**: ~$0.05 per GB per month (standard warm storage)
- **Cross-region data transfer**: $0.02 per GB
- **Restore operations**: $0.02 per GB

### Usage-Based Cost Examples

**Light Development Usage** (2-3 hours/day, 5 days/week)
- **Voice interactions**: ~50 conversations/week
- **Average conversation**: 4-6 exchanges
- **Estimated monthly cost**: $8-15

**Moderate Testing** (Daily usage, multiple team members)
- **Voice interactions**: ~200 conversations/week
- **Extended conversations**: 8-10 exchanges each
- **Estimated monthly cost**: $25-45

**Heavy Development** (Continuous testing, multiple environments)
- **Voice interactions**: ~500+ conversations/week
- **Complex operations**: Long-running AWS tasks
- **Estimated monthly cost**: $60-100+

### Cost Optimization Features

The solution includes several built-in cost controls:
- **Voice response truncation**: Limited to 800 characters to reduce token usage
- **Efficient agent routing**: Minimizes unnecessary LLM calls
- **Conversation management**: Sliding window to control context size
- **Free tier utilization**: Leverages AWS free tier services where available

### Cost Factors That Impact Pricing

1. **Conversation Length**: Longer conversations consume more tokens
2. **Voice vs Text**: Voice processing costs more than text-only interactions
3. **AWS Operations**: Complex operations requiring multiple API calls
4. **Instance Usage**: EC2 instances for testing (can be stopped when not needed)
5. **Backup Storage**: Depends on data volume being backed up

### Production Considerations

For production deployments, additional costs may include:
- **Load balancing**: Application Load Balancer (~$16/month)
- **High availability**: Multi-AZ deployments
- **Monitoring**: CloudWatch logs and metrics
- **Security**: WAF, additional IAM roles
- **Scaling**: Auto Scaling groups and larger instance types

**Important Notes:**
- Pricing shown is for US East (N. Virginia) region as of August 2025
- Actual costs depend heavily on usage patterns and conversation frequency
- The voice-optimized design helps keep token usage predictable
- Consider using AWS Cost Explorer and budgets for monitoring

## 🛠️ Prerequisites

- **Python 3.12+** with pip
- **Node.js 16+** and npm
- **AWS Account** with access to:
  - AWS Bedrock (Claude 3 Haiku model)
  - Amazon Nova Sonic
  - EC2, SSM, and AWS Backup services
- **AWS CLI** configured with appropriate credentials
- **Audio hardware** (microphone and speakers for voice mode)

## 📦 Installation & Implementation Guide

### Step 1: Backend Setup

**Clone and prepare the environment:**
```bash
# Clone the repository
git clone <repository-url>
cd sample-aws-strands-nova-voice-assistant

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Unix/macOS
# or
.venv\Scripts\activate  # On Windows

# Install Python dependencies
pip install -r requirements.txt
```

### Step 2: Configure AWS Service Authentication

This application uses two different AWS authentication mechanisms:

**Nova Sonic Integration**: Requires AWS credentials as environment variables
**Other AWS Services**: Uses boto3 with AWS profiles

**Set up AWS credentials for Nova Sonic (required as environment variables):**
```bash
export AWS_ACCESS_KEY_ID=<your-access-key-id>
export AWS_SECRET_ACCESS_KEY=<your-secret-access-key>
export AWS_SESSION_TOKEN=<your-session-token>  # Only if using temporary credentials
export AWS_DEFAULT_REGION=<your-region>
```

**Configure AWS CLI profile for other services:**
```bash
aws configure --profile <your-profile-name>
# Enter your AWS Access Key ID, Secret Access Key, and default region
```

**Apply the required IAM permissions to your AWS user/role:**
- Amazon Bedrock model invocation
- EC2 instance management  
- SSM operations
- AWS Backup functionality
- Supporting services (KMS, STS)

**Test your configuration:**
```bash
# Test AWS CLI access
aws sts get-caller-identity --profile <your-profile-name>

# Test environment variables
echo $AWS_ACCESS_KEY_ID
```

**Security Note**: Follow the principle of least privilege - grant only permissions needed for your specific use case. Customize the provided IAM policy based on which AWS services you plan to use with the voice assistant.

AWS Permissions Example:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "BedrockPermissions",
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel",
                "bedrock:InvokeModelWithResponseStream",
                "bedrock:GetFoundationModel",
                "bedrock:ListFoundationModels"
            ],
            "Resource": "*"
        },
        {
            "Sid": "EC2ReadPermissions",
            "Effect": "Allow",
            "Action": [
                "ec2:DescribeInstances",
                "ec2:DescribeSecurityGroups",
                "ec2:DescribeImages",
                "ec2:DescribeVpcs",
                "ec2:DescribeInstanceStatus"
            ],
            "Resource": "*"
        },
        {
            "Sid": "EC2WritePermissions",
            "Effect": "Allow",
            "Action": [
                "ec2:StartInstances",
                "ec2:StopInstances",
                "ec2:RebootInstances"
            ],
            "Resource": "*"
        },
        {
            "Sid": "SSMReadPermissions",
            "Effect": "Allow",
            "Action": [
                "ssm:DescribeInstanceInformation",
                "ssm:GetCommandInvocation",
                "ssm:ListCommands",
                "ssm:ListCommandInvocations",
                "ssm:DescribeDocument",
                "ssm:ListDocuments"
            ],
            "Resource": "*"
        },
        {
            "Sid": "SSMWritePermissions",
            "Effect": "Allow",
            "Action": [
                "ssm:SendCommand",
                "ssm:StartSession",
                "ssm:CreateDocument"
            ],
            "Resource": "*"
        },
        {
            "Sid": "BackupReadPermissions",
            "Effect": "Allow",
            "Action": [
                "backup:ListBackupJobs",
                "backup:DescribeBackupVault",
                "backup:ListBackupPlans",
                "backup:ListBackupVaults",
                "backup:DescribeBackupJob"
            ],
            "Resource": "*"
        },
        {
            "Sid": "BackupWritePermissions",
            "Effect": "Allow",
            "Action": [
                "backup:CreateBackupVault",
                "backup:CreateBackupPlan",
                "backup:StartBackupJob",
                "backup:StartRestoreJob"
            ],
            "Resource": "*"
        },
        {
            "Sid": "BackupStoragePermissions",
            "Effect": "Allow",
            "Action": [
                "backup-storage:StartObject",
                "backup-storage:PutObject",
                "backup-storage:ListObjects"
            ],
            "Resource": "*"
        },
        {
            "Sid": "SupportingPermissions",
            "Effect": "Allow",
            "Action": [
                "kms:DescribeKey",
                "sts:GetCallerIdentity"
            ],
            "Resource": "*"
        }
    ]
}
```

### Step 3: Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install Node.js dependencies
npm install
```

### Step 4: Launch the Application

**Start the backend server:**
```bash
# From the project root (recommended)
./run_backend.sh

# Or with custom parameters:
./run_backend.sh --profile <your-profile> --region <your-region> --voice matthew
```

**Start the frontend in a new terminal:**
```bash
# Development mode (recommended)
./run_frontend.sh

# Or manually:
cd frontend
npm start
```

### Step 5: Configure Voice Settings (Optional)

The system supports multiple voice options for text-to-speech:
```bash
# Use different voice options
./run_backend.sh --voice matthew  # Default male voice
./run_backend.sh --voice tiffany  # Female voice option
./run_backend.sh --voice amy      # Alternative female voice
```

### Using the Application

1. **Start the backend server** as described above
2. **Start the React frontend** in development mode
3. **Open your browser** to http://localhost:3000
4. **Configure WebSocket URL** if needed (default: ws://localhost:8080)
5. **Click "Start Conversation"** to begin voice interaction
6. **Grant microphone permissions** when prompted

### Important Notes

- **Default port changed**: The default backend port is now 8080 (changed from 80 to avoid requiring administrator privileges). If you need to use a different port:
  ```bash
  # Use a custom port
  ./run_backend.sh --port 3001
  ```
  Then update the WebSocket URL in the frontend to match your chosen port

- **AWS Profile**: Make sure your AWS profile has the necessary permissions for Bedrock and other AWS services

## 🎯 Supported Operations

### EC2 Agent
- List and describe EC2 instances
- Start, stop, and reboot instances
- Instance status monitoring
- Security group and VPC information

### SSM Agent
- Execute commands on instances
- Patch management operations
- Parameter Store interactions
- Session Manager connections

### Backup Agent
- List backup jobs and vaults
- Configure backup plans
- Monitor backup status
- Restore operations

## Cleanup
To avoid ongoing charges, clean up your resources when you're done testing:
- Terminate any test instances created during the demo
- Remove the custom IAM roles and policies created for this solution
- Remove any backup plans or vaults created while testing
- Delete any snapshots or AMI’s created during the tests

## 🛠️ Troubleshooting

If you encounter issues during setup or operation, these common solutions can help resolve most problems:

### Audio Configuration
- Ensure microphone permissions are granted in the browser
- Try using Firefox for better Web Audio API compatibility
- Verify system audio settings are configured correctly

### WebSocket Connection Issues
- Verify the backend server is running on the correct port
- Check firewall settings for WebSocket traffic
- Ensure the frontend WebSocket URL matches the backend configuration

### AWS Service Permissions
- Verify IAM policies include necessary service permissions
- Check AWS CLI configuration and credentials
- Ensure the AWS profile has access to required regions

## 🔧 Development Notes

### Architecture Design
- **Simple session management** without complex recovery mechanisms
- **Basic WebSocket server** without automatic reconnection loops
- **Straightforward tool processing** with the supervisor agent
- **Clean error handling** that asks users to restart rather than automatic recovery

### Key Design Decisions
- **Single Tool**: Uses one `supervisorAgent` tool that routes to specialized agents
- **Voice Optimization**: Responses truncated to 800 characters for better voice experience
- **User-Controlled Recovery**: When errors occur, users manually restart conversations

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

For issues and questions:
- Check the troubleshooting section above
- Review AWS service documentation
- Ensure all prerequisites are met
- Verify AWS permissions and credentials


## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License
This library is licensed under the MIT-0 License. See the LICENSE file.

