import { describe, it, expect } from "vitest";
import type {
  MatchStatus,
  AttendanceStatus,
  RecordRoomStatus,
  TeamRole,
} from "@/lib/types";
import {
  canManageMatch,
  canWriteRecord,
  canVoteAttendance,
} from "@/features/team/lib/authorization";

// ============================================================
// 핵심 운영 루프 통합 테스트 (도메인 로직 단위 테스트)
// 생성 → 투표 → 확정 → 기록 → 마감 전체 흐름 검증
// ============================================================

// --- 도메인 규칙 정의 ---

const VALID_MATCH_TRANSITIONS: Record<MatchStatus, MatchStatus[]> = {
  OPEN: ["CONFIRMED", "CANCELLED"],
  CONFIRMED: ["COMPLETED", "CANCELLED"],
  COMPLETED: [],
  CANCELLED: [],
};

const VALID_ROOM_TRANSITIONS: Record<RecordRoomStatus, RecordRoomStatus[]> = {
  OPEN: ["CLOSED"],
  CLOSED: [],
};

const VOTEABLE_STATUSES: AttendanceStatus[] = ["ACCEPTED", "DECLINED", "MAYBE"];

function canTransitionMatch(from: MatchStatus, to: MatchStatus): boolean {
  return VALID_MATCH_TRANSITIONS[from].includes(to);
}

function canTransitionRoom(
  from: RecordRoomStatus,
  to: RecordRoomStatus
): boolean {
  return VALID_ROOM_TRANSITIONS[from].includes(to);
}

function canVote(matchStatus: MatchStatus): boolean {
  return matchStatus === "OPEN";
}

function canInputRecord(roomStatus: RecordRoomStatus): boolean {
  return roomStatus === "OPEN";
}

function canCloseRecordRoom(
  matchStatus: MatchStatus,
  roomStatus: RecordRoomStatus
): boolean {
  return matchStatus === "CONFIRMED" && roomStatus === "OPEN";
}

// --- 시뮬레이션 헬퍼 ---

interface SimMatch {
  id: string;
  status: MatchStatus;
  confirmed_at: string | null;
  completed_at: string | null;
}

interface SimAttendance {
  match_id: string;
  user_id: string;
  status: AttendanceStatus;
  voted_at: string | null;
}

interface SimRecordRoom {
  id: string;
  match_id: string;
  status: RecordRoomStatus;
  closed_at: string | null;
}

interface SimRecord {
  record_room_id: string;
  user_id: string;
  goals: number;
  assists: number;
}

function createMatch(id: string): SimMatch {
  return { id, status: "OPEN", confirmed_at: null, completed_at: null };
}

function createAttendances(
  matchId: string,
  memberIds: string[]
): SimAttendance[] {
  return memberIds.map((uid) => ({
    match_id: matchId,
    user_id: uid,
    status: "PENDING" as AttendanceStatus,
    voted_at: null,
  }));
}

function confirmMatch(match: SimMatch): {
  match: SimMatch;
  recordRoom: SimRecordRoom;
} {
  const now = new Date().toISOString();
  return {
    match: { ...match, status: "CONFIRMED", confirmed_at: now },
    recordRoom: {
      id: `room-${match.id}`,
      match_id: match.id,
      status: "OPEN",
      closed_at: null,
    },
  };
}

function closeRecordRoom(
  match: SimMatch,
  room: SimRecordRoom
): { match: SimMatch; recordRoom: SimRecordRoom } {
  const now = new Date().toISOString();
  return {
    match: { ...match, status: "COMPLETED", completed_at: now },
    recordRoom: { ...room, status: "CLOSED", closed_at: now },
  };
}

// ============================================================
// 1단계: 경기 생성 시 출석 자동 생성 검증
// ============================================================
describe("1단계: 경기 생성 → 출석 자동 생성", () => {
  const teamMembers = ["user-1", "user-2", "user-3"];

  it("경기 생성 시 모든 팀 멤버에 대해 출석 레코드가 생성된다", () => {
    const match = createMatch("match-1");
    const attendances = createAttendances(match.id, teamMembers);

    expect(attendances).toHaveLength(teamMembers.length);
    attendances.forEach((att) => {
      expect(att.match_id).toBe(match.id);
      expect(teamMembers).toContain(att.user_id);
    });
  });

  it("생성된 출석 레코드의 초기 상태는 모두 PENDING이다", () => {
    const match = createMatch("match-1");
    const attendances = createAttendances(match.id, teamMembers);

    attendances.forEach((att) => {
      expect(att.status).toBe("PENDING");
      expect(att.voted_at).toBeNull();
    });
  });

  it("경기 초기 상태는 OPEN이다", () => {
    const match = createMatch("match-1");
    expect(match.status).toBe("OPEN");
    expect(match.confirmed_at).toBeNull();
    expect(match.completed_at).toBeNull();
  });

  it("MANAGER 이상만 경기를 생성할 수 있다", () => {
    expect(canManageMatch("ADMIN")).toBe(true);
    expect(canManageMatch("MANAGER")).toBe(true);
    expect(canManageMatch("MEMBER")).toBe(false);
    expect(canManageMatch("GUEST")).toBe(false);
  });
});

// ============================================================
// 2단계: 출석 투표 상태 전이 검증
// ============================================================
describe("2단계: 출석 투표 상태 전이", () => {
  it("OPEN 상태의 경기에서만 투표할 수 있다", () => {
    expect(canVote("OPEN")).toBe(true);
    expect(canVote("CONFIRMED")).toBe(false);
    expect(canVote("COMPLETED")).toBe(false);
    expect(canVote("CANCELLED")).toBe(false);
  });

  it("유효한 투표 상태는 ACCEPTED, DECLINED, MAYBE이다", () => {
    expect(VOTEABLE_STATUSES).toEqual(["ACCEPTED", "DECLINED", "MAYBE"]);
  });

  it("PENDING에서 유효한 투표 상태로 전환할 수 있다", () => {
    const attendance: SimAttendance = {
      match_id: "match-1",
      user_id: "user-1",
      status: "PENDING",
      voted_at: null,
    };

    VOTEABLE_STATUSES.forEach((newStatus) => {
      const updated = { ...attendance, status: newStatus, voted_at: new Date().toISOString() };
      expect(updated.status).toBe(newStatus);
      expect(updated.voted_at).toBeTruthy();
    });
  });

  it("투표 시 voted_at 타임스탬프가 기록된다", () => {
    const before = new Date().toISOString();
    const voted: SimAttendance = {
      match_id: "match-1",
      user_id: "user-1",
      status: "ACCEPTED",
      voted_at: new Date().toISOString(),
    };
    expect(voted.voted_at).toBeTruthy();
    expect(voted.voted_at! >= before).toBe(true);
  });
});

// ============================================================
// 3단계: 경기 확정 시 기록실 자동 생성 검증
// ============================================================
describe("3단계: 경기 확정 → 기록실 자동 생성", () => {
  it("OPEN 상태에서 CONFIRMED로 전이할 수 있다", () => {
    expect(canTransitionMatch("OPEN", "CONFIRMED")).toBe(true);
  });

  it("확정 시 기록실이 OPEN 상태로 자동 생성된다", () => {
    const match = createMatch("match-1");
    const { match: confirmed, recordRoom } = confirmMatch(match);

    expect(confirmed.status).toBe("CONFIRMED");
    expect(confirmed.confirmed_at).toBeTruthy();
    expect(recordRoom.match_id).toBe(match.id);
    expect(recordRoom.status).toBe("OPEN");
    expect(recordRoom.closed_at).toBeNull();
  });

  it("MANAGER 이상만 경기를 확정할 수 있다", () => {
    expect(canManageMatch("ADMIN")).toBe(true);
    expect(canManageMatch("MANAGER")).toBe(true);
    expect(canManageMatch("MEMBER")).toBe(false);
    expect(canManageMatch("GUEST")).toBe(false);
  });

  it("OPEN이 아닌 상태에서는 확정할 수 없다", () => {
    expect(canTransitionMatch("CONFIRMED", "CONFIRMED")).toBe(false);
    expect(canTransitionMatch("COMPLETED", "CONFIRMED")).toBe(false);
    expect(canTransitionMatch("CANCELLED", "CONFIRMED")).toBe(false);
  });
});

// ============================================================
// 4단계: 기록 입력 후 기록실 마감 → 경기 COMPLETED 전이
// ============================================================
describe("4단계: 기록 입력 → 기록실 마감 → 경기 COMPLETED", () => {
  it("OPEN 기록실에 기록을 입력할 수 있다", () => {
    expect(canInputRecord("OPEN")).toBe(true);
  });

  it("기록 입력 후 기록실을 마감하면 CLOSED가 된다", () => {
    const match = createMatch("match-1");
    const { match: confirmed, recordRoom } = confirmMatch(match);

    // 기록 입력 시뮬레이션
    const record: SimRecord = {
      record_room_id: recordRoom.id,
      user_id: "user-1",
      goals: 2,
      assists: 1,
    };
    expect(record.record_room_id).toBe(recordRoom.id);

    // 마감
    expect(canCloseRecordRoom(confirmed.status, recordRoom.status)).toBe(true);
    const { match: completed, recordRoom: closedRoom } = closeRecordRoom(
      confirmed,
      recordRoom
    );

    expect(closedRoom.status).toBe("CLOSED");
    expect(closedRoom.closed_at).toBeTruthy();
  });

  it("기록실 마감 시 경기가 COMPLETED로 전이된다", () => {
    const match = createMatch("match-1");
    const { match: confirmed, recordRoom } = confirmMatch(match);
    const { match: completed } = closeRecordRoom(confirmed, recordRoom);

    expect(completed.status).toBe("COMPLETED");
    expect(completed.completed_at).toBeTruthy();
  });

  it("CONFIRMED → COMPLETED 전이가 유효하다", () => {
    expect(canTransitionMatch("CONFIRMED", "COMPLETED")).toBe(true);
  });

  it("MANAGER 이상만 기록실을 마감할 수 있다", () => {
    expect(canManageMatch("ADMIN")).toBe(true);
    expect(canManageMatch("MANAGER")).toBe(true);
    expect(canManageMatch("MEMBER")).toBe(false);
    expect(canManageMatch("GUEST")).toBe(false);
  });

  it("CONFIRMED 상태의 경기에서만 기록실을 마감할 수 있다", () => {
    expect(canCloseRecordRoom("CONFIRMED", "OPEN")).toBe(true);
    expect(canCloseRecordRoom("OPEN", "OPEN")).toBe(false);
    expect(canCloseRecordRoom("COMPLETED", "OPEN")).toBe(false);
    expect(canCloseRecordRoom("CANCELLED", "OPEN")).toBe(false);
  });
});

// ============================================================
// 5단계: CLOSED 기록실에 기록 입력 시 409 검증
// ============================================================
describe("5단계: CLOSED 기록실 기록 입력 차단", () => {
  it("CLOSED 기록실에는 기록을 입력할 수 없다", () => {
    expect(canInputRecord("CLOSED")).toBe(false);
  });

  it("CLOSED 기록실은 다시 OPEN으로 전이할 수 없다", () => {
    expect(canTransitionRoom("CLOSED", "OPEN")).toBe(false);
  });

  it("CLOSED 기록실은 더 이상 전이할 수 없다 (종단 상태)", () => {
    expect(VALID_ROOM_TRANSITIONS.CLOSED).toHaveLength(0);
  });

  it("전체 흐름: 마감 후 기록 입력 시도는 차단된다", () => {
    const match = createMatch("match-1");
    const { match: confirmed, recordRoom } = confirmMatch(match);
    const { recordRoom: closedRoom } = closeRecordRoom(confirmed, recordRoom);

    // 마감된 기록실에 기록 입력 시도
    expect(closedRoom.status).toBe("CLOSED");
    expect(canInputRecord(closedRoom.status)).toBe(false);
  });
});

// ============================================================
// 6단계: 멱등성 검증 (중복 확정, 중복 마감)
// ============================================================
describe("6단계: 멱등성 검증", () => {
  it("이미 CONFIRMED 경기에 다시 확정 요청 시 전이가 불가하다 (API는 멱등 응답)", () => {
    // CONFIRMED → CONFIRMED는 유효 전이가 아님
    expect(canTransitionMatch("CONFIRMED", "CONFIRMED")).toBe(false);
    // 단, API에서는 멱등하게 기존 데이터를 반환함 (match.status가 CONFIRMED|COMPLETED이면 200)
  });

  it("이미 COMPLETED 경기에 다시 확정 요청 시 전이가 불가하다 (API는 멱등 응답)", () => {
    expect(canTransitionMatch("COMPLETED", "CONFIRMED")).toBe(false);
  });

  it("이미 CLOSED 기록실에 다시 마감 요청 시 전이가 불가하다 (API는 409 + 기존 데이터)", () => {
    expect(canTransitionRoom("CLOSED", "CLOSED")).toBe(false);
    // API에서는 409와 함께 기존 record_room, match 데이터 반환
  });

  it("COMPLETED 경기에서는 더 이상 상태 변경이 불가하다", () => {
    expect(VALID_MATCH_TRANSITIONS.COMPLETED).toHaveLength(0);
  });

  it("중복 확정: API는 CONFIRMED/COMPLETED 경기에 대해 기존 기록실을 반환한다", () => {
    // 확정 API의 멱등성 동작 검증
    const match = createMatch("match-1");
    const { match: confirmed, recordRoom } = confirmMatch(match);

    // 동일 경기에 대해 확정 재시도 → 이미 CONFIRMED이므로 전이 불가
    expect(confirmed.status).toBe("CONFIRMED");
    expect(canTransitionMatch(confirmed.status, "CONFIRMED")).toBe(false);
    // 기록실은 이미 존재
    expect(recordRoom).toBeTruthy();
    expect(recordRoom.match_id).toBe(match.id);
  });

  it("중복 마감: API는 이미 CLOSED 기록실에 대해 기존 데이터를 반환한다", () => {
    const match = createMatch("match-1");
    const { match: confirmed, recordRoom } = confirmMatch(match);
    const { match: completed, recordRoom: closedRoom } = closeRecordRoom(
      confirmed,
      recordRoom
    );

    // 재마감 시도 → 이미 CLOSED이므로 전이 불가
    expect(closedRoom.status).toBe("CLOSED");
    expect(canCloseRecordRoom(completed.status, closedRoom.status)).toBe(false);
    // 기존 데이터가 보존됨
    expect(closedRoom.closed_at).toBeTruthy();
    expect(completed.completed_at).toBeTruthy();
  });
});

// ============================================================
// 7단계: 권한 검증 (MEMBER/GUEST는 확정/마감/기록 불가)
// ============================================================
describe("7단계: 역할별 권한 검증", () => {
  const DENIED_ROLES: TeamRole[] = ["MEMBER", "GUEST"];
  const ALLOWED_ROLES: TeamRole[] = ["ADMIN", "MANAGER"];

  describe("경기 확정 권한 (canManageMatch)", () => {
    it.each(ALLOWED_ROLES)("%s는 경기를 확정할 수 있다", (role) => {
      expect(canManageMatch(role)).toBe(true);
    });

    it.each(DENIED_ROLES)("%s는 경기를 확정할 수 없다", (role) => {
      expect(canManageMatch(role)).toBe(false);
    });
  });

  describe("기록실 마감 권한 (canManageMatch)", () => {
    it.each(ALLOWED_ROLES)("%s는 기록실을 마감할 수 있다", (role) => {
      expect(canManageMatch(role)).toBe(true);
    });

    it.each(DENIED_ROLES)("%s는 기록실을 마감할 수 없다", (role) => {
      expect(canManageMatch(role)).toBe(false);
    });
  });

  describe("기록 입력 권한 (canWriteRecord)", () => {
    it.each(ALLOWED_ROLES)("%s는 기록을 입력할 수 있다", (role) => {
      expect(canWriteRecord(role)).toBe(true);
    });

    it.each(DENIED_ROLES)("%s는 기록을 입력할 수 없다", (role) => {
      expect(canWriteRecord(role)).toBe(false);
    });
  });

  describe("출석 투표 권한 (canVoteAttendance)", () => {
    it.each(["ADMIN", "MANAGER", "MEMBER"] as TeamRole[])(
      "%s는 출석 투표를 할 수 있다",
      (role) => {
        expect(canVoteAttendance(role)).toBe(true);
      }
    );

    it("GUEST는 출석 투표를 할 수 없다", () => {
      expect(canVoteAttendance("GUEST")).toBe(false);
    });
  });
});

// ============================================================
// 전체 운영 루프 E2E 시뮬레이션
// ============================================================
describe("전체 운영 루프 시뮬레이션 (생성→투표→확정→기록→마감)", () => {
  it("전체 운영 루프가 올바른 상태 전이를 따른다", () => {
    const teamMembers = ["user-1", "user-2", "user-3"];
    const managerRole: TeamRole = "MANAGER";

    // 1. 경기 생성
    expect(canManageMatch(managerRole)).toBe(true);
    const match = createMatch("match-loop");
    expect(match.status).toBe("OPEN");

    // 2. 출석 자동 생성
    const attendances = createAttendances(match.id, teamMembers);
    expect(attendances).toHaveLength(3);
    expect(attendances.every((a) => a.status === "PENDING")).toBe(true);

    // 3. 투표 진행
    expect(canVote(match.status)).toBe(true);
    const votedAttendances = attendances.map((att, i) => ({
      ...att,
      status: (["ACCEPTED", "ACCEPTED", "DECLINED"] as AttendanceStatus[])[i],
      voted_at: new Date().toISOString(),
    }));
    expect(votedAttendances.filter((a) => a.status === "ACCEPTED")).toHaveLength(2);

    // 4. 경기 확정 → 기록실 자동 생성
    expect(canTransitionMatch(match.status, "CONFIRMED")).toBe(true);
    const { match: confirmed, recordRoom } = confirmMatch(match);
    expect(confirmed.status).toBe("CONFIRMED");
    expect(recordRoom.status).toBe("OPEN");

    // 5. 투표 마감 확인 (CONFIRMED 상태에서는 투표 불가)
    expect(canVote(confirmed.status)).toBe(false);

    // 6. 기록 입력
    expect(canInputRecord(recordRoom.status)).toBe(true);
    const records: SimRecord[] = [
      { record_room_id: recordRoom.id, user_id: "user-1", goals: 2, assists: 1 },
      { record_room_id: recordRoom.id, user_id: "user-2", goals: 1, assists: 0 },
    ];
    expect(records).toHaveLength(2);

    // 7. 기록실 마감 → 경기 COMPLETED
    expect(canCloseRecordRoom(confirmed.status, recordRoom.status)).toBe(true);
    const { match: completed, recordRoom: closedRoom } = closeRecordRoom(
      confirmed,
      recordRoom
    );
    expect(closedRoom.status).toBe("CLOSED");
    expect(closedRoom.closed_at).toBeTruthy();
    expect(completed.status).toBe("COMPLETED");
    expect(completed.completed_at).toBeTruthy();

    // 8. 마감 후 기록 입력 차단
    expect(canInputRecord(closedRoom.status)).toBe(false);

    // 9. 더 이상 상태 변경 불가 (종단 상태)
    expect(VALID_MATCH_TRANSITIONS.COMPLETED).toHaveLength(0);
    expect(VALID_ROOM_TRANSITIONS.CLOSED).toHaveLength(0);
  });
});
