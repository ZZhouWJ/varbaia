from dataclasses import dataclass

from fastapi import HTTPException, status


@dataclass(frozen=True)
class DiskBudget:
    free_bytes: int
    estimated_media_bytes: int
    temporary_multiplier: float = 1.5
    safety_reserve_bytes: int = 2 * 1024**3

    @property
    def required_bytes(self) -> int:
        return (
            int(self.estimated_media_bytes * self.temporary_multiplier) + self.safety_reserve_bytes
        )


def enforce_disk_budget(budget: DiskBudget) -> None:
    if budget.estimated_media_bytes <= 0 or budget.free_bytes < budget.required_bytes:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="剩余磁盘空间不足，已拒绝导入以保护系统盘",
        )
