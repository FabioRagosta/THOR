from dataclasses import dataclass

lasair_token_ztf="c4b1759b3b73aa87c5cdfdc61db746be574d53fa"
lasair_token_lsst="68bf2dd0539909b916270219dd487d056b666725"

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