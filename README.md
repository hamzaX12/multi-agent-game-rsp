# Seller-Buyer Multi-Agent System

A Docker-based multi-agent communication system for simulating seller-buyer interactions using ejabberd XMPP server.

## Prerequisites

- Docker
- Docker Compose
- Git

## Getting Started

Follow these steps to set up and run the system:

### 1. Clone the Repository
```bash
git clone git@github.com:hamzaX12/seller_buyer_multi-agents.git
cd seller_buyer_multi-agents
```

### 2. Stop Old Containers (if applicable)

If you have previously run this project, stop and remove the old containers:
```bash
docker-compose down
```

### 3. Start the System

Build and start the containers:
```bash
docker-compose up --build
```

### 4. Register Agents

Open a new terminal window and register the seller and buyer agents with ejabberd:
```bash
docker-compose exec ejabberd ejabberdctl register seller localhost sellerpass
docker-compose exec ejabberd ejabberdctl register buyer localhost buyerpass
```

## Project Structure
```
seller_buyer_multi-agents/
├── Dockerfile              # Container configuration
├── docker-compose.yml      # Multi-container orchestration
├── agent.py               # Agent implementation (seller/buyer logic)
├── setup_server.py        # Server setup and initialization script
├── requirements.txt       # Python dependencies
├── .gitignore            # Git ignore file
└── ejabberd_data/        # Runtime data (not tracked in git)
```

## Usage

After completing the setup steps above, your seller and buyer agents will be registered and ready to communicate through the ejabberd XMPP server. The agents will:

- Establish XMPP connections
- Exchange messages for negotiation
- Simulate seller-buyer interactions

## Configuration

You can modify agent behaviors by editing `agent.py` and adjust server settings in `docker-compose.yml`.

## Troubleshooting

If you encounter issues:

1. **Docker issues**: Ensure Docker and Docker Compose are properly installed and running
2. **Port conflicts**: Check that no other services are using the required ports (5222, 5269, 5280)
3. **Container status**: Verify containers are running with `docker-compose ps`
4. **View logs**: Check container logs with `docker-compose logs` or `docker-compose logs ejabberd`
5. **Agent registration**: Ensure agents are properly registered before running the communication script
6. **Git issues**: If you encounter file errors with `ejabberd_data/`, ensure it's in your `.gitignore`

### Common Commands
```bash
# View running containers
docker-compose ps

# View logs
docker-compose logs -f

# Restart containers
docker-compose restart

# Stop containers
docker-compose down

# Remove all containers and volumes
docker-compose down -v
```

## Development

To contribute to this project:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Commit your changes: `git commit -am "Add new feature"`
5. Push to the branch: `git push origin feature-name`
6. Submit a pull request

## License

MIT License - feel free to use this project for educational purposes.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Contact

For questions or issues, please open an issue on the GitHub repository.
