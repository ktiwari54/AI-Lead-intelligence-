from __future__ import annotations

from dataclasses import dataclass

from backend.app.discovery.normalizers import (
    CompanyNameNormalizer,
    DomainNormalizer,
    EmailNormalizer,
    PhoneNormalizer,
    UrlNormalizer,
)
from backend.connectors.sdk.dto import ConnectorRecordDTO, NormalizedCompanyDTO, NormalizedContactDTO


@dataclass
class NormalizationStats:
    records_in: int = 0
    records_out: int = 0
    quarantined: int = 0


class NormalizationPipeline:
    """Normalize connector records into canonical DTO field formats."""

    def process(self, records: list[ConnectorRecordDTO]) -> tuple[list[ConnectorRecordDTO], NormalizationStats]:
        stats = NormalizationStats(records_in=len(records))
        output: list[ConnectorRecordDTO] = []

        for record in records:
            if record.company:
                record.company = self._normalize_company(record.company)
            if record.contact:
                record.contact = self._normalize_contact(record.contact)

            if self._is_quarantined(record):
                stats.quarantined += 1
                continue

            output.append(record)

        stats.records_out = len(output)
        return output, stats

    def _normalize_company(self, dto: NormalizedCompanyDTO) -> NormalizedCompanyDTO:
        dto.name = CompanyNameNormalizer.normalize(dto.name)
        dto.legal_name = CompanyNameNormalizer.normalize(dto.legal_name) if dto.legal_name else None
        dto.domain = DomainNormalizer.normalize(dto.domain)
        dto.website = UrlNormalizer.normalize(dto.website)
        dto.phone = PhoneNormalizer.normalize(dto.phone)
        dto.technologies = [t.strip().title() for t in dto.technologies if t and t.strip()]
        if dto.industry:
            dto.industry = dto.industry.strip().title()
        return dto

    def _normalize_contact(self, dto: NormalizedContactDTO) -> NormalizedContactDTO:
        dto.first_name = dto.first_name.strip().title() if dto.first_name else ""
        dto.last_name = dto.last_name.strip().title() if dto.last_name else ""
        dto.email = EmailNormalizer.normalize(dto.email)
        dto.phone = PhoneNormalizer.normalize(dto.phone)
        dto.company_domain = DomainNormalizer.normalize(dto.company_domain)
        dto.company_name = CompanyNameNormalizer.normalize(dto.company_name) if dto.company_name else None
        if dto.title:
            dto.title = dto.title.strip()
        return dto

    def _is_quarantined(self, record: ConnectorRecordDTO) -> bool:
        if record.entity_type == "company" and record.company:
            return not record.company.name
        if record.entity_type == "contact" and record.contact:
            return not record.contact.first_name and not record.contact.email
        return True