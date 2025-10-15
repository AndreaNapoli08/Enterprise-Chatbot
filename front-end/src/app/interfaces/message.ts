export interface Message {
  text?: string;
  image?: string;
  role: 'user' | 'bot';
  time: string;
}