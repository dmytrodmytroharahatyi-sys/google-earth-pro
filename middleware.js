/**
 * Vercel Edge Middleware for Basic Authentication
 * Protects all KML endpoints with username/password
 */

export const config = {
    matcher: ['/kml', '/kml/data', '/webhook/:path*'],
};

export default function middleware(req) {
    const basicAuth = req.headers.get('authorization');
    const url = req.nextUrl;

    // Get credentials from environment variables
    const USERNAME = process.env.BASIC_AUTH_USER || 'admin';
    const PASSWORD = process.env.BASIC_AUTH_PASSWORD || '';

    // If no password is set, allow access (development mode)
    if (!PASSWORD) {
        return;
    }

    // Check if authorization header is present
    if (basicAuth) {
        const authValue = basicAuth.split(' ')[1];
        const [user, pwd] = atob(authValue).split(':');

        // Verify credentials
        if (user === USERNAME && pwd === PASSWORD) {
            return; // Allow access
        }
    }

    // Authentication failed or not provided
    return new Response('Authentication required', {
        status: 401,
        headers: {
            'WWW-Authenticate': 'Basic realm="Secure Area"',
        },
    });
}
