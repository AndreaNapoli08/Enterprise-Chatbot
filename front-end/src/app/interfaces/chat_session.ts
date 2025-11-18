export interface ChatSession {
  id: string;
  title: string | null;
  user_email: string;
  created_at: string;
  last_activity: string | null;
  active: boolean;
}