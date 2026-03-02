import axios from "axios";

export interface SignupPayload {
  email: string;
  password: string;
  name: string;
}

export interface SignupResponse {
  user: { id: string; email: string; name: string };
}

export interface MeResponse {
  user: {
    id: string;
    email: string;
    name: string;
    avatar_url: string | null;
    created_at: string;
  };
}

export async function signup(payload: SignupPayload): Promise<SignupResponse> {
  const { data } = await axios.post<SignupResponse>("/api/auth/signup", payload);
  return data;
}

export async function getMe(): Promise<MeResponse> {
  const { data } = await axios.get<MeResponse>("/api/auth/me");
  return data;
}
