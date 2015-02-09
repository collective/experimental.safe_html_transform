import os
import transaction

from plone.testing import Layer
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import FunctionalTesting
from plone.app.testing import TEST_USER_NAME, TEST_USER_PASSWORD
from plone.testing import z2


class SeleniumLayer(Layer):
    defaultBases = (z2.ZSERVER_FIXTURE, )

    def testSetUp(self):
        # Start up Selenium
        driver = os.environ.get('SELENIUM_DRIVER', '').lower() or 'firefox'
        webdriver = __import__(
            'selenium.webdriver.%s.webdriver' % driver, fromlist=['WebDriver'])
        args = [arg.strip() for arg in
                os.environ.get('SELENIUM_ARGS', '').split()
                if arg.strip()]
        self['selenium'] = webdriver.WebDriver(*args)

    def testTearDown(self):
        self['selenium'].quit()
        del self['selenium']

SELENIUM_FIXTURE = SeleniumLayer()
SELENIUM_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(SELENIUM_FIXTURE, ),
    name="SeleniumTesting:Functional")
SELENIUM_PLONE_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(SELENIUM_FIXTURE, PLONE_FIXTURE),
    name="SeleniumTesting:Functional")


# Helper functions


def open(selenium, url):
    # ensure we have a clean starting point
    transaction.commit()
    selenium.get(url)


def login(selenium, portal, username=False, password=False):

    if not username:
        username = TEST_USER_NAME
    if not password:
        password = TEST_USER_PASSWORD

    open(selenium, portal.absolute_url() + '/login_form')
    selenium.find_element_by_name('__ac_name').send_keys(username)
    selenium.find_element_by_name('__ac_password').send_keys(password)
    selenium.find_element_by_name('submit').click()


def click(selenium, xpath):
    if xpath.count("link="):
        link = xpath.split("link=")[-1]
        element = selenium.find_element_by_partial_link_text(link)
    elif xpath.count("//"):
        element = selenium.find_element_by_xpath(xpath)
    elif xpath.count('#'):
        eleName = xpath.split("#")[-1]
        element = selenium.find_element_by_id(eleName)
    else:
        element = selenium.find_element_by_name(xpath)

    element.click()


def type(selenium, name, value):
    selenium.find_element_by_name(name).send_keys(value)


def typeMce(selenium, value):
    '''
    Text fields with mce are different.We need to go into the frame and update the
    p element to make this work. Unfortunately the code to get out of the frame is not
    implemented in python yet. The workaround is to use this handle trick, which
    is currently unsupported in chrome. See issue #405 for more. In general there
    are still a lot of open issues on frame support so if this breaks it won't
    be a surprise.'''
    handle = selenium.current_window_handle
    selenium.switch_to_frame("form.text_ifr")
    ele = selenium.find_element_by_xpath("//p")
    ele.send_keys(value)
    selenium.switch_to_window(handle)


def clear(selenium, name):
    selenium.find_element_by_name(name).clear()


def select(selenium, xpath1, xpath2=''):
    xpath = xpath1
    if xpath2:
        xpath = "%s['%s']"%(xpath1, xpath2)
        xpath = xpath.replace("select['label=", "select/option['text()=")
    selenium.find_element_by_xpath(xpath).click()


def waitForPageToLoad(selenium, foo):
    # this does nothing but make us lazy folks happy
    pass


def publish(selenium):
    click(selenium, "//dl[@id='plone-contentmenu-workflow']/dt/a")
    click(selenium, "#workflow-transition-publish")


def submit(selenium, formId):
    selenium.find_element_by_id(formId).submit()
