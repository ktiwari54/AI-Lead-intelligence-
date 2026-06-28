import { NextResponse } from 'next/server'

const AUTH_COOKIE = 'ai_lead_authenticated'
const MAX_AGE = 60 * 60 * 24 * 30

export async function POST() {
  const response = NextResponse.json({ ok: true })
  response.cookies.set(AUTH_COOKIE, '1', {
    path: '/',
    maxAge: MAX_AGE,
    sameSite: 'lax',
  })
  return response
}

export async function DELETE() {
  const response = NextResponse.json({ ok: true })
  response.cookies.set(AUTH_COOKIE, '', {
    path: '/',
    maxAge: 0,
    sameSite: 'lax',
  })
  return response
}