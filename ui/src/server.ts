import { createServer } from 'http';

const server = createServer();

// Set longer timeouts for the HTTP server
server.keepAliveTimeout = 41 * 60 * 1000;  // 41 minutes
server.headersTimeout = 42 * 60 * 1000;    // 42 minutes
server.requestTimeout = 43 * 60 * 1000;    // 43 minutes

export default server; 