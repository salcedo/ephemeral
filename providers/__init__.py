from providers.atlantic import EphemeralProviderAtlantic
from providers.aws import EphemeralProviderAWS
from providers.digital import EphemeralProviderDigitalOcean
from providers.gce import EphemeralProviderGoogleCompute
from providers.vultr import EphemeralProviderVultr


Providers = {
    'atlantic': EphemeralProviderAtlantic,
    'aws': EphemeralProviderAWS,
    'digitalocean': EphemeralProviderDigitalOcean,
    'google_compute': EphemeralProviderGoogleCompute,
    'vultr': EphemeralProviderVultr
}
