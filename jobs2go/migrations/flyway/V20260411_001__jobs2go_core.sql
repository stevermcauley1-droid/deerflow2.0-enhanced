-- Jobs2Go core schema (pilot v1)
-- Postgres 14+

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Core users and verification
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  role TEXT NOT NULL CHECK (role IN ('employer','worker','both','admin')),
  email TEXT UNIQUE,
  phone TEXT UNIQUE,
  password_hash TEXT,
  status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active','suspended','banned','pending')),
  country_code CHAR(2),
  locale TEXT DEFAULT 'en-US',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE user_verifications (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  kyc_status TEXT NOT NULL DEFAULT 'unverified' CHECK (kyc_status IN ('unverified','pending','verified','failed')),
  kyc_provider TEXT,
  kyc_reference TEXT,
  face_liveness_passed BOOLEAN,
  background_check_status TEXT CHECK (background_check_status IN ('not_requested','pending','passed','failed')),
  verified_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (user_id)
);

-- Worker profile
CREATE TABLE worker_profiles (
  user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  display_name TEXT NOT NULL,
  bio TEXT,
  intro_video_url TEXT,
  location_lat DOUBLE PRECISION,
  location_lng DOUBLE PRECISION,
  service_radius_km NUMERIC(6,2) DEFAULT 15.0,
  is_available_now BOOLEAN NOT NULL DEFAULT false,
  reliability_score NUMERIC(5,4) DEFAULT 0.5000,
  response_time_p50_sec INTEGER,
  acceptance_rate NUMERIC(5,4),
  completion_rate NUMERIC(5,4),
  rating_avg NUMERIC(3,2) DEFAULT 0.00,
  rating_count INTEGER NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE skills (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  code TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  category TEXT NOT NULL,
  is_active BOOLEAN NOT NULL DEFAULT true
);

CREATE TABLE worker_skills (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  worker_id UUID NOT NULL REFERENCES worker_profiles(user_id) ON DELETE CASCADE,
  skill_id UUID NOT NULL REFERENCES skills(id),
  level TEXT NOT NULL CHECK (level IN ('hobbyist','experienced','expert')),
  verified BOOLEAN NOT NULL DEFAULT false,
  verification_source TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (worker_id, skill_id)
);

CREATE TABLE worker_service_preferences (
  worker_id UUID PRIMARY KEY REFERENCES worker_profiles(user_id) ON DELETE CASCADE,
  accepts_paid BOOLEAN NOT NULL DEFAULT true,
  accepts_teaching BOOLEAN NOT NULL DEFAULT false,
  accepts_volunteering BOOLEAN NOT NULL DEFAULT false,
  accepts_hobbies BOOLEAN NOT NULL DEFAULT false,
  do_jobs JSONB NOT NULL DEFAULT '[]'::jsonb,
  dont_jobs JSONB NOT NULL DEFAULT '[]'::jsonb,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE worker_rates (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  worker_id UUID NOT NULL REFERENCES worker_profiles(user_id) ON DELETE CASCADE,
  skill_id UUID REFERENCES skills(id),
  rate_type TEXT NOT NULL CHECK (rate_type IN ('hourly','daily','fixed')),
  currency CHAR(3) NOT NULL DEFAULT 'USD',
  amount_cents INTEGER NOT NULL CHECK (amount_cents >= 0),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (worker_id, skill_id, rate_type, currency)
);

CREATE TABLE worker_availability_slots (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  worker_id UUID NOT NULL REFERENCES worker_profiles(user_id) ON DELETE CASCADE,
  starts_at TIMESTAMPTZ NOT NULL,
  ends_at TIMESTAMPTZ NOT NULL,
  recurrence_rule TEXT,
  timezone TEXT DEFAULT 'UTC',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (ends_at > starts_at)
);

-- Jobs, matching, offers, bookings
CREATE TABLE jobs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  employer_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  title TEXT NOT NULL,
  description TEXT NOT NULL,
  category_code TEXT NOT NULL,
  skill_level TEXT CHECK (skill_level IN ('hobbyist','experienced','expert')),
  location_mode TEXT NOT NULL CHECK (location_mode IN ('onsite','remote','hybrid')),
  location_lat DOUBLE PRECISION,
  location_lng DOUBLE PRECISION,
  address_text TEXT,
  start_window_from TIMESTAMPTZ,
  start_window_to TIMESTAMPTZ,
  urgency TEXT CHECK (urgency IN ('now','same_day','scheduled')),
  budget_type TEXT CHECK (budget_type IN ('hourly','daily','fixed')),
  budget_min_cents INTEGER CHECK (budget_min_cents >= 0),
  budget_max_cents INTEGER CHECK (budget_max_cents >= 0),
  currency CHAR(3) NOT NULL DEFAULT 'USD',
  ai_parse_confidence NUMERIC(5,4),
  ai_parse_payload JSONB,
  status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('draft','open','offered','accepted','in_progress','completed','cancelled','expired','disputed')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE job_requirements (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
  skill_id UUID NOT NULL REFERENCES skills(id),
  weight NUMERIC(5,4) DEFAULT 1.0,
  UNIQUE (job_id, skill_id)
);

CREATE TABLE job_matches (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
  worker_id UUID NOT NULL REFERENCES worker_profiles(user_id) ON DELETE CASCADE,
  score NUMERIC(6,5) NOT NULL,
  rank_position INTEGER NOT NULL,
  distance_km NUMERIC(7,3),
  eta_minutes INTEGER,
  explanation JSONB NOT NULL DEFAULT '[]'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (job_id, worker_id)
);

CREATE TABLE offers (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
  employer_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  worker_id UUID NOT NULL REFERENCES worker_profiles(user_id) ON DELETE RESTRICT,
  message TEXT,
  proposed_amount_cents INTEGER NOT NULL CHECK (proposed_amount_cents >= 0),
  currency CHAR(3) NOT NULL DEFAULT 'USD',
  status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','accepted','declined','expired','cancelled')),
  expires_at TIMESTAMPTZ,
  responded_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE bookings (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  job_id UUID NOT NULL UNIQUE REFERENCES jobs(id) ON DELETE CASCADE,
  offer_id UUID NOT NULL UNIQUE REFERENCES offers(id) ON DELETE RESTRICT,
  employer_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  worker_id UUID NOT NULL REFERENCES worker_profiles(user_id) ON DELETE RESTRICT,
  starts_at TIMESTAMPTZ,
  ended_at TIMESTAMPTZ,
  status TEXT NOT NULL DEFAULT 'accepted' CHECK (status IN ('accepted','in_progress','completed','cancelled','disputed','settled')),
  completion_notes TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Messaging
CREATE TABLE chats (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  job_id UUID REFERENCES jobs(id) ON DELETE SET NULL,
  employer_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  worker_id UUID NOT NULL REFERENCES worker_profiles(user_id) ON DELETE CASCADE,
  is_active BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (job_id, employer_id, worker_id)
);

CREATE TABLE messages (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  chat_id UUID NOT NULL REFERENCES chats(id) ON DELETE CASCADE,
  sender_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  message_type TEXT NOT NULL DEFAULT 'text' CHECK (message_type IN ('text','image','video','system')),
  body TEXT,
  attachment_url TEXT,
  moderation_status TEXT NOT NULL DEFAULT 'clear' CHECK (moderation_status IN ('clear','flagged','blocked')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Payments and ledger
CREATE TABLE payments (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  booking_id UUID NOT NULL UNIQUE REFERENCES bookings(id) ON DELETE RESTRICT,
  employer_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  worker_id UUID NOT NULL REFERENCES worker_profiles(user_id) ON DELETE RESTRICT,
  provider TEXT NOT NULL,
  provider_payment_ref TEXT,
  currency CHAR(3) NOT NULL DEFAULT 'USD',
  gross_amount_cents INTEGER NOT NULL CHECK (gross_amount_cents >= 0),
  platform_fee_cents INTEGER NOT NULL CHECK (platform_fee_cents >= 0),
  worker_payout_cents INTEGER NOT NULL CHECK (worker_payout_cents >= 0),
  escrow_status TEXT NOT NULL CHECK (escrow_status IN ('authorized','captured','released','refunded','failed')),
  paid_at TIMESTAMPTZ,
  released_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE ledger_entries (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  payment_id UUID REFERENCES payments(id) ON DELETE SET NULL,
  booking_id UUID REFERENCES bookings(id) ON DELETE SET NULL,
  account_code TEXT NOT NULL,
  direction TEXT NOT NULL CHECK (direction IN ('debit','credit')),
  amount_cents INTEGER NOT NULL CHECK (amount_cents >= 0),
  currency CHAR(3) NOT NULL DEFAULT 'USD',
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Reputation, trust, disputes
CREATE TABLE reviews (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  booking_id UUID NOT NULL REFERENCES bookings(id) ON DELETE CASCADE,
  reviewer_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  reviewee_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  rating SMALLINT NOT NULL CHECK (rating BETWEEN 1 AND 5),
  comment TEXT,
  is_public BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (booking_id, reviewer_id, reviewee_id)
);

CREATE TABLE trust_events (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
  event_type TEXT NOT NULL,
  risk_score NUMERIC(5,4),
  action_taken TEXT,
  details JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE disputes (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  booking_id UUID NOT NULL UNIQUE REFERENCES bookings(id) ON DELETE CASCADE,
  raised_by UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  reason_code TEXT NOT NULL,
  description TEXT,
  status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open','under_review','resolved','rejected')),
  resolution JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Notifications and audit
CREATE TABLE notifications (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  channel TEXT NOT NULL CHECK (channel IN ('push','sms','email','in_app')),
  template_code TEXT NOT NULL,
  payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  status TEXT NOT NULL DEFAULT 'queued' CHECK (status IN ('queued','sent','failed','read')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  sent_at TIMESTAMPTZ
);

CREATE TABLE audit_logs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  actor_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
  action TEXT NOT NULL,
  resource_type TEXT NOT NULL,
  resource_id UUID,
  ip_address INET,
  user_agent TEXT,
  diff JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Indexes
CREATE INDEX idx_jobs_employer_status ON jobs (employer_id, status, created_at DESC);
CREATE INDEX idx_jobs_location ON jobs (location_mode, location_lat, location_lng);
CREATE INDEX idx_job_matches_job_rank ON job_matches (job_id, rank_position);
CREATE INDEX idx_offers_worker_status ON offers (worker_id, status, created_at DESC);
CREATE INDEX idx_bookings_worker_status ON bookings (worker_id, status, created_at DESC);
CREATE INDEX idx_messages_chat_created ON messages (chat_id, created_at DESC);
CREATE INDEX idx_ledger_booking ON ledger_entries (booking_id, created_at DESC);
CREATE INDEX idx_trust_user_created ON trust_events (user_id, created_at DESC);
CREATE INDEX idx_reviews_reviewee_created ON reviews (reviewee_id, created_at DESC);
CREATE INDEX idx_notifications_user_status ON notifications (user_id, status, created_at DESC);
