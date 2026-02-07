/**
 * Vercel Edge Middleware - Basic Authentication
 * Protects all routes with username/password authentication
 */

import { NextResponse } from 'next/server';

export const config = {
  matcher: '/(.*)',
};

export function middleware(req) {
  // Get credentials from environment variables
  const AUTH_USERNAME = process.env.AUTH_USERNAME || 'admin';
  const AUTH_PASSWORD = process.env.AUTH_PASSWORD;

  // Skip authentication if password is not set (for development)
  if (!AUTH_PASSWORD) {
    console.warn('AUTH_PASSWORD not set - authentication is disabled!');
    return NextResponse.next();
  }

  // Get the authorization header
  const authHeader = req.headers.get('authorization');

  // If no auth header, request authentication
  if (!authHeader) {
    return new NextResponse('Authentication required', {
      status: 401,
      headers: {
        'WWW-Authenticate': 'Basic realm="Secure Area"',
      },
    });
  }

  // Parse the authorization header
  const auth = authHeader.split(' ')[1];
  const [username, password] = Buffer.from(auth, 'base64').toString().split(':');

  // Verify credentials
  if (username === AUTH_USERNAME && password === AUTH_PASSWORD) {
    // Authentication successful
    return NextResponse.next();
  }

  // Authentication failed
  return new NextResponse('Invalid credentials', {
    status: 401,
    headers: {
      'WWW-Authenticate': 'Basic realm="Secure Area"',
    },
  });
}
