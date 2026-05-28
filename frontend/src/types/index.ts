export interface User {
  id: string
  email: string
}

export interface Dataset {
  id: string
  asin: string
  product_name: string | null
  product_url: string | null
  status: 'pending' | 'scraping' | 'ready' | 'error'
  review_count: number | null
  avg_star_rating: number | null
  review_date_min: string | null
  review_date_max: string | null
  error_message: string | null
  created_at: string
  last_scraped_at: string | null
  created_by: string | null
}

export interface Review {
  id: string
  star_rating: number
  reviewer_name: string | null
  review_date: string | null
  verified_purchase: boolean
  helpful_votes: number
  review_text: string
  sentiment_label: string | null
}

export interface ReviewsResponse {
  total: number
  page: number
  per_page: number
  reviews: Review[]
}

export interface Theme {
  theme: string
  frequency: number
}

export interface SentimentCount {
  count: number
  pct: number
}

export interface Summary {
  stats: {
    review_count: number
    avg_star_rating: number | null
    review_date_min: string | null
    review_date_max: string | null
    verified_count: number
    unverified_count: number
  }
  sentiment: {
    positive: SentimentCount
    neutral: SentimentCount
    negative: SentimentCount
  }
  themes: Theme[]
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  scope_refused?: boolean
}

export interface RateLimitStatus {
  daily_limit: number
  reviews_fetched_today: number
  suspended: boolean
  next_scrape_available_at: string | null
}
