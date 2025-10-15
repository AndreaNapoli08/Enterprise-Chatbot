export interface Message {
  text?: string;
  image?: string;
  buttons?: { title: string, payload: string }[];
  role: 'user' | 'bot';
  time: string;
}