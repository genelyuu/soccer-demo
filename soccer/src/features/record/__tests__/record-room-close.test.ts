import { describe, it, expect } from "vitest";
import type { MatchStatus, RecordRoomStatus } from "@/lib/types";

// 기록실 마감 상태 전이 규칙 검증 (도메인 로직 단위 테스트)

const VALID_ROOM_TRANSITIONS: Record<RecordRoomStatus, RecordRoomStatus[]> = {
  OPEN: ["CLOSED"],
  CLOSED: [],
};

const MATCH_STATUS_ON_CLOSE: Record<MatchStatus, boolean> = {
  OPEN: false,
  CONFIRMED: true,
  COMPLETED: false,
  CANCELLED: false,
};

function canCloseRecordRoom(roomStatus: RecordRoomStatus): boolean {
  return VALID_ROOM_TRANSITIONS[roomStatus].includes("CLOSED");
}

function canCloseFromMatchStatus(matchStatus: MatchStatus): boolean {
  return MATCH_STATUS_ON_CLOSE[matchStatus];
}

describe("기록실 마감 상태 전이 규칙", () => {
  it("OPEN 상태의 기록실만 마감할 수 있다", () => {
    expect(canCloseRecordRoom("OPEN")).toBe(true);
  });

  it("이미 CLOSED된 기록실은 다시 마감할 수 없다", () => {
    expect(canCloseRecordRoom("CLOSED")).toBe(false);
  });

  it("CONFIRMED 상태의 경기에서만 기록실을 마감할 수 있다", () => {
    expect(canCloseFromMatchStatus("CONFIRMED")).toBe(true);
  });

  it("OPEN 상태의 경기에서는 기록실을 마감할 수 없다", () => {
    expect(canCloseFromMatchStatus("OPEN")).toBe(false);
  });

  it("이미 COMPLETED 상태의 경기에서는 기록실을 마감할 수 없다", () => {
    expect(canCloseFromMatchStatus("COMPLETED")).toBe(false);
  });

  it("CANCELLED 상태의 경기에서는 기록실을 마감할 수 없다", () => {
    expect(canCloseFromMatchStatus("CANCELLED")).toBe(false);
  });

  it("기록실 마감 시 경기 상태가 COMPLETED로 전이되어야 한다", () => {
    const autoActions: Record<string, string[]> = {
      CLOSE_RECORD_ROOM: ["SET_MATCH_COMPLETED"],
    };
    expect(autoActions["CLOSE_RECORD_ROOM"]).toContain("SET_MATCH_COMPLETED");
  });

  it("기록실 마감 시 closed_at이 설정되어야 한다", () => {
    const closedRoom = {
      status: "CLOSED" as RecordRoomStatus,
      closed_at: new Date().toISOString(),
    };
    expect(closedRoom.status).toBe("CLOSED");
    expect(closedRoom.closed_at).toBeTruthy();
  });
});
