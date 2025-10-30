export interface Message {
  text?: string;
  image?: string;
  buttons?: { title: string, payload: string }[];
  attachment?: { type: string; url: string }; 
  role: 'user' | 'bot';
  time: string;
  elapsedSeconds?: number | null;
}