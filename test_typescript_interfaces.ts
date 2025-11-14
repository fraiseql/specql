// Sample TypeScript interfaces for testing
export interface User {
  id: number;
  email: string;
  name?: string;
  age: number;
  isActive: boolean;
  createdAt: Date;
  profile?: UserProfile;
  posts: Post[];
  tags: string[];
  metadata: any;
}

export interface UserProfile {
  id: number;
  bio?: string;
  avatarUrl?: string;
  userId: number;
  settings: UserSettings;
}

export interface UserSettings {
  theme: 'light' | 'dark';
  notifications: boolean;
  language: string;
}

export interface Post {
  id: number;
  title: string;
  content?: string;
  published: boolean;
  authorId: number;
  tags: string[];
  createdAt: Date;
  updatedAt: Date;
}

export interface Comment {
  id: number;
  content: string;
  postId: number;
  authorId: number;
  createdAt: Date;
  parentId?: number;
}

// Type aliases
export type PostStatus = 'draft' | 'published' | 'archived';

export type UserRole = 'admin' | 'moderator' | 'user';

export type ApiResponse<T> = {
  success: boolean;
  data?: T;
  error?: string;
  timestamp: Date;
};