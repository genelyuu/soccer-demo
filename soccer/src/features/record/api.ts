import axios from "axios";
import type { RecordRoom, MatchRecord, RecordWithUser } from "@/lib/types";

export interface RecordRoomResponse {
  record_room: RecordRoom;
  records: RecordWithUser[];
}

export interface RecordPayload {
  user_id: string;
  goals: number;
  assists: number;
  yellow_cards: number;
  red_cards: number;
  memo?: string;
}

export async function getRecordRoom(matchId: string): Promise<RecordRoomResponse> {
  const { data } = await axios.get(`/api/matches/${matchId}/record`);
  return data;
}

export async function submitRecord(matchId: string, payload: RecordPayload): Promise<{ record: MatchRecord }> {
  const { data } = await axios.post(`/api/matches/${matchId}/record`, payload);
  return data;
}

export async function closeRecordRoom(matchId: string): Promise<{ record_room: RecordRoom; match: { id: string; status: string } }> {
  const { data } = await axios.patch(`/api/matches/${matchId}/record/close`);
  return data;
}
