"""
Compatibility helper mod of Jovian for NCBI Taxonomy rank-name changes.

NCBI discontinued the rank name "superkingdom" in 2025. Jovian keeps the
legacy output column to avoid breaking downstream reports, but derives it from
the current rankedlineage.dmp "domain/realm" field when needed.

Author: Thijmen van der loop, Wageningen Food Safety Reseach (Thijmen.vanderloop@wur.nl)
"""

LEGACY_TOP_LEVEL_COLUMN = "superkingdom"
DOMAIN_OR_REALM_COLUMN = "domain_or_realm"

TOP_LEVEL_TAXA = ["Archaea", "Bacteria", "Eukaryota", "Viruses"]

VIRAL_REALMS = [
    "Adnaviria",
    "Duplodnaviria",
    "Monodnaviria",
    "Riboviria",
    "Ribozyviria",
    "Varidnaviria",
]

VIRAL_ROOTS = ["Viruses", "Acellular root", "acellular root"]


def strip_object_columns(df):
    """Strip whitespace from string-like dataframe columns in place."""
    for column in df.columns:
        df[column] = df[column].map(
            lambda value: value.strip() if isinstance(value, str) else value
        )
    return df


def is_virus_record(record):
    """Return True for legacy virus records and current NCBI viral realm records."""
    values = {
        record.get("tax_name"),
        record.get(LEGACY_TOP_LEVEL_COLUMN),
        record.get(DOMAIN_OR_REALM_COLUMN),
    }
    return any(value in VIRAL_ROOTS or value in VIRAL_REALMS for value in values)


def derive_legacy_superkingdom(record):
    """
    Derive Jovian's legacy top-level bucket from legacy or current NCBI fields.

    Current rankedlineage.dmp stores the final field as domain/realm. For
    cellular organisms this is usually Archaea, Bacteria, or Eukaryota. For
    viruses it can be a viral realm, while the Viruses node itself is ranked as
    acellular root.
    """
    legacy_value = record.get(LEGACY_TOP_LEVEL_COLUMN)
    if legacy_value in TOP_LEVEL_TAXA:
        return legacy_value

    domain_or_realm = record.get(DOMAIN_OR_REALM_COLUMN)
    if domain_or_realm in TOP_LEVEL_TAXA[:3]:
        return domain_or_realm

    if is_virus_record(record):
        return "Viruses"

    return legacy_value


def add_legacy_superkingdom(df):
    """Populate Jovian's legacy superkingdom column from current taxonomy data."""
    if (
        DOMAIN_OR_REALM_COLUMN not in df.columns
        and LEGACY_TOP_LEVEL_COLUMN not in df.columns
    ):
        df[LEGACY_TOP_LEVEL_COLUMN] = None
        return df
    df[LEGACY_TOP_LEVEL_COLUMN] = df.apply(derive_legacy_superkingdom, axis=1)
    return df
