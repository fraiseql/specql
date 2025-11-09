/**
 * Sample generated TypeScript types
 * This file shows what the TypeScriptTypesGenerator produces
 */

import { gql } from '@apollo/client';

// Base scalar types
export type UUID = string;
export type DateTime = string;
export type Date = string;
export type Time = string;
export type Interval = string;
export type JSONValue = any;

// GraphQL operation result wrapper
export interface MutationResult<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  code?: string;
}

// Pagination types
export interface PaginationInput {
  limit?: number;
  offset?: number;
  orderBy?: string;
  orderDirection?: 'ASC' | 'DESC';
}

export interface PaginatedResult<T> {
  items: T[];
  totalCount: number;
  hasNextPage: boolean;
  hasPreviousPage: boolean;
}

// Contact Entity
export interface Contact {
  id: UUID;
  first_name: string;
  last_name: string;
  email?: string;
  created_at: DateTime;
}

export interface ContactInput {
  first_name: string;
  last_name: string;
  email?: string;
}

export interface ContactFilter {
  id?: UUID;
  first_name?: string;
  last_name?: string;
  email?: string;
  created_at?: DateTime;
  first_name_gt?: string;
  first_name_lt?: string;
  last_name_gt?: string;
  last_name_lt?: string;
  email_gt?: string;
  email_lt?: string;
  email_like?: string;
  email_ilike?: string;
  created_at_gt?: DateTime;
  created_at_lt?: DateTime;
}

// Contact create_contact mutation types
export interface CreateContactInput {
  first_name: string;
  last_name: string;
  email?: string;
}

export interface CreateContactSuccess {
  contact: Contact;
  message: string;
}

export interface CreateContactError {
  code: string;
  message: string;
  details?: any;
}

export type CreateContactResult = CreateContactSuccess | CreateContactError;

// Contact update_contact mutation types
export interface UpdateContactInput {
  id: UUID;
  first_name?: string;
  last_name?: string;
  email?: string;
}

export interface UpdateContactSuccess {
  contact: Contact;
  message: string;
}

export interface UpdateContactError {
  code: string;
  message: string;
  details?: any;
}

export type UpdateContactResult = UpdateContactSuccess | UpdateContactError;

// Contact delete_contact mutation types
export interface DeleteContactInput {
  id: UUID;
}

export interface DeleteContactSuccess {
  success: boolean;
  message: string;
}

export interface DeleteContactError {
  code: string;
  message: string;
  details?: any;
}

export type DeleteContactResult = DeleteContactSuccess | DeleteContactError;