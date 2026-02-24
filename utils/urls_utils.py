from urllib.parse import urlparse


class UrlsUtils:
    @staticmethod
    def normalize_grafana_base_url(raw_base_url: str) -> str:
        if not raw_base_url or not raw_base_url.strip():
            raise ValueError("Grafana URL is required.")
        trimmed_base_url = raw_base_url.strip()
        parsed_url = urlparse(trimmed_base_url)
        if parsed_url.scheme and parsed_url.netloc:
            return f"{parsed_url.scheme}://{parsed_url.netloc}"
        raise ValueError(f"Grafana URL must include scheme and host. Value is '{raw_base_url}'.")

    @staticmethod
    def normalize_atlassian_base_url(raw_domain: str) -> str:
        if not raw_domain:
            raise ValueError(
                "ATLASSIAN_DOMAIN is required (e.g., 'ippen.atlassian.net' "
                "or 'https://ippen.atlassian.net')."
            )
        raw_domain = raw_domain.strip()
        if not raw_domain:
            raise ValueError(
                "ATLASSIAN_DOMAIN is required (e.g., 'ippen.atlassian.net' "
                "or 'https://ippen.atlassian.net')."
            )

        if raw_domain.startswith(("http://", "https://")):
            parsed = urlparse(raw_domain)
            if not parsed.netloc:
                raise ValueError(
                    "ATLASSIAN_DOMAIN must include a host "
                    "(e.g., 'https://ippen.atlassian.net')."
                )
            return f"{parsed.scheme}://{parsed.netloc}"

        host = raw_domain.split("/", 1)[0]
        return f"https://{host}"


if __name__ == "__main__":
    print(UrlsUtils.normalize_grafana_base_url("https://grafana.example.com/path"))
