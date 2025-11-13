/**
 * Mock Authentication Service
 *
 * Provides a local authentication system that mimics Supabase's interface.
 * Perfect for local development and fast iteration without external dependencies.
 *
 * When ready to migrate to real Supabase, simply swap this implementation
 * in the auth context without changing any UI components.
 */

export interface User {
  id: string
  email: string
  user_metadata: {
    provider: 'email' | 'google' | 'github'
    full_name?: string
    avatar_url?: string
  }
  created_at: string
}

export interface Session {
  user: User
  token: string
  expires_at: string
}

export interface AuthError {
  message: string
  status?: number
}

export interface AuthResponse {
  user: User | null
  session: Session | null
  error: AuthError | null
}

// Mock users database (pre-seeded with test accounts)
// User 1 matches the backend mock user ID for perfect sync!
const MOCK_USERS: User[] = [
  {
    id: '00000000-0000-0000-0000-000000000001', // Matches backend mock user!
    email: 'local@test.dev',
    user_metadata: {
      provider: 'email',
      full_name: 'Local Test User',
    },
    created_at: new Date().toISOString(),
  },
  {
    id: '00000000-0000-0000-0000-000000000002',
    email: 'demo@example.com',
    user_metadata: {
      provider: 'email',
      full_name: 'Demo User',
    },
    created_at: new Date().toISOString(),
  },
  {
    id: '00000000-0000-0000-0000-000000000003',
    email: 'admin@cyberintel.dev',
    user_metadata: {
      provider: 'email',
      full_name: 'Admin User',
    },
    created_at: new Date().toISOString(),
  },
  {
    id: '00000000-0000-0000-0000-000000000004',
    email: 'testuser@example.com',
    user_metadata: {
      provider: 'email',
      full_name: 'Test User',
    },
    created_at: new Date().toISOString(),
  },
]

// Simple password store (in real app, would be hashed)
const MOCK_PASSWORDS: Record<string, string> = {
  'local@test.dev': 'password123',
  'demo@example.com': 'demo123',
  'admin@cyberintel.dev': 'admin123',
  'testuser@example.com': 'test123',
}

// Storage keys
const SESSION_KEY = 'mock-auth-session'
const USER_STORE_KEY = 'mock-auth-users'

// Helper to generate fake JWT-like token
function generateMockToken(userId: string): string {
  const header = btoa(JSON.stringify({ alg: 'MOCK', typ: 'JWT' }))
  const payload = btoa(
    JSON.stringify({
      sub: userId,
      exp: Date.now() + 24 * 60 * 60 * 1000, // 24 hours
      iat: Date.now(),
    })
  )
  const signature = btoa(`mock-signature-${userId}`)
  return `${header}.${payload}.${signature}`
}

// Helper to generate UUID v4
function generateUUID(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0
    const v = c === 'x' ? r : (r & 0x3) | 0x8
    return v.toString(16)
  })
}

// Initialize user store from localStorage
function getUserStore(): User[] {
  if (typeof window === 'undefined') return MOCK_USERS

  const stored = localStorage.getItem(USER_STORE_KEY)
  if (stored) {
    try {
      return JSON.parse(stored)
    } catch {
      return MOCK_USERS
    }
  }

  // Initialize with default users
  localStorage.setItem(USER_STORE_KEY, JSON.stringify(MOCK_USERS))
  return MOCK_USERS
}

// Save user store to localStorage
function saveUserStore(users: User[]): void {
  if (typeof window === 'undefined') return
  localStorage.setItem(USER_STORE_KEY, JSON.stringify(users))
}

// Get all passwords (including dynamically added ones)
function getPasswordStore(): Record<string, string> {
  if (typeof window === 'undefined') return MOCK_PASSWORDS

  const stored = localStorage.getItem('mock-auth-passwords')
  if (stored) {
    try {
      return JSON.parse(stored)
    } catch {
      return MOCK_PASSWORDS
    }
  }
  return MOCK_PASSWORDS
}

// Save password store
function savePasswordStore(passwords: Record<string, string>): void {
  if (typeof window === 'undefined') return
  localStorage.setItem('mock-auth-passwords', JSON.stringify(passwords))
}

/**
 * Mock Auth Class
 * Mimics Supabase auth interface
 */
export class MockAuth {
  /**
   * Sign in with email and password
   */
  async signInWithPassword({
    email,
    password,
  }: {
    email: string
    password: string
  }): Promise<AuthResponse> {
    // Simulate network delay
    await new Promise((resolve) => setTimeout(resolve, 300))

    const users = getUserStore()
    const passwords = getPasswordStore()

    // Find user
    const user = users.find((u) => u.email === email)
    if (!user) {
      return {
        user: null,
        session: null,
        error: { message: 'Invalid email or password', status: 401 },
      }
    }

    // Check password
    if (passwords[email] !== password) {
      return {
        user: null,
        session: null,
        error: { message: 'Invalid email or password', status: 401 },
      }
    }

    // Create session
    const token = generateMockToken(user.id)
    const session: Session = {
      user,
      token,
      expires_at: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
    }

    // Save session to localStorage
    if (typeof window !== 'undefined') {
      localStorage.setItem(SESSION_KEY, JSON.stringify(session))
    }

    return { user, session, error: null }
  }

  /**
   * Sign up with email and password
   */
  async signUp({
    email,
    password,
  }: {
    email: string
    password: string
  }): Promise<AuthResponse> {
    // Simulate network delay
    await new Promise((resolve) => setTimeout(resolve, 400))

    const users = getUserStore()
    const passwords = getPasswordStore()

    // Check if user already exists
    if (users.some((u) => u.email === email)) {
      return {
        user: null,
        session: null,
        error: { message: 'User already exists', status: 400 },
      }
    }

    // Validate email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!emailRegex.test(email)) {
      return {
        user: null,
        session: null,
        error: { message: 'Invalid email format', status: 400 },
      }
    }

    // Validate password strength
    if (password.length < 6) {
      return {
        user: null,
        session: null,
        error: { message: 'Password must be at least 6 characters', status: 400 },
      }
    }

    // Create new user
    const newUser: User = {
      id: generateUUID(),
      email,
      user_metadata: {
        provider: 'email',
        full_name: email.split('@')[0],
      },
      created_at: new Date().toISOString(),
    }

    // Save user and password
    users.push(newUser)
    passwords[email] = password
    saveUserStore(users)
    savePasswordStore(passwords)

    // Create session
    const token = generateMockToken(newUser.id)
    const session: Session = {
      user: newUser,
      token,
      expires_at: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
    }

    // Save session
    if (typeof window !== 'undefined') {
      localStorage.setItem(SESSION_KEY, JSON.stringify(session))
    }

    return { user: newUser, session, error: null }
  }

  /**
   * Sign in with OAuth provider (mock implementation)
   */
  async signInWithOAuth({
    provider,
  }: {
    provider: 'google' | 'github'
  }): Promise<AuthResponse> {
    // Simulate OAuth flow delay
    await new Promise((resolve) => setTimeout(resolve, 500))

    // Generate mock OAuth user
    const email = `${provider}-user-${Date.now()}@example.com`
    const users = getUserStore()

    const newUser: User = {
      id: generateUUID(),
      email,
      user_metadata: {
        provider,
        full_name: `${provider.charAt(0).toUpperCase() + provider.slice(1)} User`,
        avatar_url: `https://api.dicebear.com/7.x/avataaars/svg?seed=${email}`,
      },
      created_at: new Date().toISOString(),
    }

    // Save user
    users.push(newUser)
    saveUserStore(users)

    // Create session
    const token = generateMockToken(newUser.id)
    const session: Session = {
      user: newUser,
      token,
      expires_at: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
    }

    // Save session
    if (typeof window !== 'undefined') {
      localStorage.setItem(SESSION_KEY, JSON.stringify(session))
    }

    return { user: newUser, session, error: null }
  }

  /**
   * Sign out
   */
  async signOut(): Promise<{ error: AuthError | null }> {
    // Simulate network delay
    await new Promise((resolve) => setTimeout(resolve, 200))

    if (typeof window !== 'undefined') {
      localStorage.removeItem(SESSION_KEY)
    }

    return { error: null }
  }

  /**
   * Get current session from localStorage
   */
  async getSession(): Promise<{ data: { session: Session | null }; error: AuthError | null }> {
    if (typeof window === 'undefined') {
      return { data: { session: null }, error: null }
    }

    const stored = localStorage.getItem(SESSION_KEY)
    if (!stored) {
      return { data: { session: null }, error: null }
    }

    try {
      const session: Session = JSON.parse(stored)

      // Check if session is expired
      if (new Date(session.expires_at) < new Date()) {
        localStorage.removeItem(SESSION_KEY)
        return { data: { session: null }, error: null }
      }

      return { data: { session }, error: null }
    } catch {
      return { data: { session: null }, error: null }
    }
  }

  /**
   * Get current user
   */
  async getUser(): Promise<{ data: { user: User | null }; error: AuthError | null }> {
    const { data } = await this.getSession()
    return { data: { user: data.session?.user || null }, error: null }
  }

  /**
   * Listen to auth state changes (mock implementation)
   */
  onAuthStateChange(callback: (event: string, session: Session | null) => void) {
    // Check session on mount
    this.getSession().then(({ data }) => {
      callback('INITIAL_SESSION', data.session)
    })

    // Return unsubscribe function
    return {
      data: {
        subscription: {
          unsubscribe: () => {
            // Mock unsubscribe
          },
        },
      },
    }
  }
}

// Export singleton instance
export const mockAuth = new MockAuth()
