import uuid
import factory
from factory import fuzzy

from apps.company.models import (
    StartupProfile,
    CompanyMember,
    StartupServiceProduct,
    TargetedMarket,
    DevelopmentStage,
)
from apps.accounts.user.tests.factories import AnyUserFactory, create_founder_user


class StartupProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = StartupProfile

    startup_name = factory.Faker("company")
    startup_industry = factory.Faker("job")
    website_link = factory.Faker("url")
    location = factory.Faker("city")
    founded_year = fuzzy.FuzzyInteger(2000, 2025)
    bio = factory.Faker("paragraph")
    is_verified = False
    is_public = True
    is_active = True

    
    primary_founder = factory.LazyFunction(lambda: create_founder_user())

    @factory.post_generation
    def members(self, create, extracted, **kwargs):
        if not create or not extracted:
            return
        
        if isinstance(extracted, int):
            for _ in range(extracted):
                CompanyMemberFactory(startup=self)
        else:
            for member_kwargs in extracted:
                CompanyMemberFactory(startup=self, **member_kwargs)

    @factory.post_generation
    def services_and_products(self, create, extracted, **kwargs):
        if not create or not extracted:
            return
        if isinstance(extracted, int):
            for i in range(extracted):
                StartupServiceProductFactory(startup=self, name=f"Service {i+1}")
        else:
            for svc_kwargs in extracted:
                StartupServiceProductFactory(startup=self, **svc_kwargs)

    @factory.post_generation
    def targeted_markets(self, create, extracted, **kwargs):
        if not create or not extracted:
            return
        if isinstance(extracted, int):
            for _ in range(extracted):
                TargetedMarketFactory(startup=self)
        else:
            for market_kwargs in extracted:
                TargetedMarketFactory(startup=self, **market_kwargs)


class CompanyMemberFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CompanyMember

    startup = factory.SubFactory(StartupProfileFactory)
    user = factory.SubFactory(AnyUserFactory)
    member_type = fuzzy.FuzzyChoice([
        "founder", "co_founder", "employee", "advisor", "consultant", "intern", "contractor"
    ])
    position = factory.Faker("job")
    is_current = True
    is_primary_contact = False


class StartupServiceProductFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = StartupServiceProduct

    startup = factory.SubFactory(StartupProfileFactory)
    name = factory.Faker("catch_phrase")
    description = factory.Faker("sentence")
    is_active = True


class TargetedMarketFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TargetedMarket

    startup = factory.SubFactory(StartupProfileFactory)
    market_type = fuzzy.FuzzyChoice(["local", "gcc", "mena", "global"])
    market_name = factory.Faker("word")
    market_size = factory.Faker("pydecimal", left_digits=4, right_digits=2, positive=True)
    market_share = factory.Faker("pydecimal", left_digits=2, right_digits=2, positive=True)
    description = factory.Faker("sentence")
    is_primary = False



def create_startup_with_members(services_count: int = 0, members_count: int = 1, **kwargs) -> StartupProfile:
    startup = StartupProfileFactory(services_and_products=services_count, members=members_count, **kwargs)
    return startup


def create_company_member(**kwargs) -> CompanyMember:
    return CompanyMemberFactory(**kwargs)


