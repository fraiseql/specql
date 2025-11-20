# Time & Scheduling Domain

> **Status**: 🚧 Documentation in Progress
>
> This stdlib domain is planned but not yet fully documented. Check back soon!

## Overview

The Time domain provides temporal data entities and scheduling support for applications that need to manage calendars, timezones, and date ranges.

## Coming Soon

This documentation will cover:
- [ ] Calendar entity - Business calendar with holidays
- [ ] Timezone entity - IANA timezone database integration
- [ ] DateRange entity - Time periods with validation
- [ ] Recurring events and schedules
- [ ] Holiday management
- [ ] Business day calculations

## Planned Entities

### Calendar
Business calendar with holiday support.

```yaml
# Coming soon
entity: Calendar
schema: time
fields:
  name: text!
  timezone: timezone!
  holidays: list(date)
```

### Timezone
IANA timezone database.

```yaml
# Coming soon
entity: Timezone
schema: time
fields:
  code: text!  # e.g., "America/New_York"
  offset: integer!
  dst_active: boolean
```

### DateRange
Time periods with validation.

```yaml
# Coming soon
entity: DateRange
schema: time
fields:
  start_date: date!
  end_date: date!
  # Validates: end_date >= start_date
```

## Related Documentation

- [stdlib Overview](../index.md) - All stdlib domains
- [CRM Domain](../crm/index.md) - Customer relationship entities
- [I18n Domain](../i18n/index.md) - Internationalization entities

## Questions?

If you need this domain urgently:
- Check the [stdlib overview](../index.md) for available domains
- Open an issue on GitHub requesting priority
- Consider contributing! See [Extending stdlib](../../07_advanced/extending-stdlib.md)

---

*Last Updated*: 2025-11-20
