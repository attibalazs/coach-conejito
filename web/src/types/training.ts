export interface DualLoadBlock {
  ctl: number;
  atl: number;
  tsb: number;
}

export interface Polarization {
  easy_pct: number;
  tempo_pct: number;
  hard_pct: number;
}

export interface CrossTrainingSummary {
  cycling_sessions: number;
  cycling_km: number;
  strength_sessions: number;
}

export interface WeekSummary {
  week: string;
  start_date: string;
  end_date: string;
  sessions: number;
  distance_km: number;
  duration_min: number;
  elevation_gain_m: number;
  elevation_loss_m: number;
  impact_score: number;
  cardio_score: number;
  speed_score?: number;
  impact_to_cardio_ratio: number | null;
  avg_hr: number | null;
  avg_cadence: number | null;
  avg_gct_ms: number | null;
  avg_vertical_oscillation_cm: number | null;
  avg_stride_length_m: number | null;
  aerobic_efficiency: number | null;
  avg_decoupling_pct: number | null;
  polarization: Polarization;
  monotony_7d: number | null;
  strain_7d: number | null;
  injury_risk_score?: number | null;
  injury_risk_level?: string | null;
  acwr?: number | null;
  risk_factors?: string[];
  cross_training?: CrossTrainingSummary;
}

export interface PeriodSummary extends Omit<WeekSummary, "week"> {
  dual_load: {
    impact: DualLoadBlock;
    cardio: DualLoadBlock;
    speed?: DualLoadBlock;
  };
  delta_vs_previous?: {
    distance_pct: number | null;
    impact_pct: number | null;
    cardio_pct: number | null;
    efficiency_pct: number | null;
  };
}

export interface ActivityItem {
  id: string;
  date: string;
  source: string;
  name: string | null;
  type: string | null;
  distance_km: number;
  duration_min: number;
  elevation_gain_m: number | null;
  elevation_loss_m: number | null;
  avg_hr: number | null;
  max_hr: number | null;
  cadence: number | null;
  gct_ms: number | null;
  vertical_oscillation_cm: number | null;
  stride_length_m: number | null;
  impact_score: number;
  cardio_score: number;
  gap_pace_sec_per_km: number | null;
  decoupling_pct: number | null;
}

export interface WellnessEntry {
  date: string;
  resting_hr: number | null;
  hrv_ms: number | null;
  sleep_score: number | null;
  sleep_duration_sec: number | null;
  body_battery_high: number | null;
  stress_avg: number | null;
}

export interface JournalEntry {
  date: string;
  rpe: number | null;
  mood: string | null;
  soreness: number | null;
  notes: string | null;
}

export interface TrainingExport {
  user_id: string;
  window: {
    start: string;
    end: string;
    days: number;
  };
  summary: PeriodSummary;
  weekly_trends: WeekSummary[];
  activities: ActivityItem[];
  wellness: WellnessEntry[];
  journals: JournalEntry[];
}
