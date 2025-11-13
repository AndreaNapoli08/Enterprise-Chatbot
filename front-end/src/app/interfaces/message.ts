export interface Message {
  text?: string;
  image?: string;
  custom?: { type?: string;  text?: string;  [key: string]: any; };
  buttons?: { title: string, payload: string }[];
  attachment?: { type: string; url: string; name: string, size: number, pages: number }; 
  role: 'user' | 'bot';
  time: string;
  elapsedSeconds?: number | null;
  disabled?: boolean;
}