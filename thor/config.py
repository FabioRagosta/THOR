from dataclasses import dataclass

lasair_token_ztf="your token for ztf query"
lasair_token_lsst="your token for lsst query"

@dataclass(slots=True)
class BrokerConfig:

    survey: str = "lsst"

    timeout: int = 30
    
    retries: int = 3
    
    verify_ssl: bool = False
    
    fink_token: str | None = None
    
    alerce_token: str | None = None
    
    lasair_token_ztf: str | None = lasair_token_ztf
    
    lasair_token_lsst: str | None = lasair_token_lsst


    def has_token(
        self,
        broker: str,
    ) -> bool:

        broker = broker.lower()
    
        if broker == "fink":
            return self.fink_token is not None
    
        if broker == "alerce":
            return self.alerce_token is not None
    
        if broker == "lasair":
            return (
                self.lasair_token_ztf is not None
                or self.lasair_token_lsst is not None
            )
    
        return False
CONFIG = BrokerConfig()
