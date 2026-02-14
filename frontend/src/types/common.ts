export interface ApiError {
  detail: string | { message: string; [key: string]: unknown };
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  skip: number;
  limit: number;
}
