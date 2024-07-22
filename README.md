# StockX: Virtual Stock Trading Platform

## Introduction

I built **StockX** to create a risk-free virtual environment where new investors like myself could learn the stock market. The lack of adequate educational stock market platforms motivated me to leverage my web development skills to build this solution.

My key goal with StockX is to provide an engaging, realistic experience for users to develop core trading skills without real financial risk. The core workflows like registering an account, managing a portfolio, buying/selling stocks, and tracking transactions mirror real brokerages. Integration with Alpha Vantage supplies real-time pricing data to mimic market conditions.  

I consciously designed the web interface to be clean, intuitive, and mobile-friendly. Interactive visualizations help users spot trends and opportunities. By focusing on learnability, my intention is for even investment novices to quickly grasp platform workflows.

### Sample
- Username: demo
- password: demo

## Video Demo

https://github.com/AUSTIN0022/StockX/assets/95069137/c7f36a98-ead7-43ab-9710-e0e53d092391

## Live Link & Local Setup

The StockX application is currently hosted at:


Demo link: https://stockx-7115.onrender.com

To run the application locally:

### Requirements

- Python 3
- Pip
- Virtualenv

### Steps 

1. Clone the repository
   ```
   git clone https://github.com/stockx/platform.git
   ```
2. Create and activate a virtual environment
   ```
   virtualenv venv --python=python3
   source venv/bin/activate
   ```  
3. Install dependencies
   ```
   pip install -r requirements.txt
   ```
4. Configure environment variables

```
ALPHA_API_KEY=sk_live_xxxx
TWILIO_SID=ACxxxxx  
TWILIO_TOKEN=xxxxxx
   
# Add other keys and secrets
```

5. Initialize the database
   ```
   python manage.py db init
   python manage.py db migrate
   python manage.py db upgrade
   ```

6. Run the development server
   ```
   python app.py
   ```
   
The app should now be running at **http://localhost:5000**! or **http://127.0.0.1:5000**!

## Existing System Overview  

The frontend utilizes my preferred stack:

- **Python Flask** for server-side logic
- **HTML/CSS/JS** for UI
- **Jinja** for dynamic templating 
- **Plotly** visualizations

I chose **SQLite** as the database for its simplicity yet robust data persistence. Hashing and salting on password fields enhances security.  

**Twilio's OTP API** enables reliable and affordable user verification during signup. Fetching live stocks data through **Alpha Vantage** supplements the realism.

My goal with the modular design was ease of enhancements. API abstractions and template inheritance should allow rapidly incorporating new features on both frontend and backend.  

Overall, from my experience across personal projects, this blend optimizes rapid development and customization at scale. Familiar languages and readable code also minimize maintenance overhead.

## Proposed System Enhancements

The charting and risk analysis upgrades I have planned align with my long-term vision for StockX. The core purpose is educating users to make informed trading decisions based on data-driven stock assessments.  

Advanced visualizations like candlestick charts, bollinger bands etc. reveal insights even for market novices. Portfolio analytics features empower users to optimize returns while minimizing risks. Incorporating sentiment analysis based on news and social media chatter adds another predictive data point.

These planned feature upgrades should heighten the educational value and real market resemblance - getting new investors primed before financial exposure. Onboarding new developers to extend platform functionality should also be straightforward via the documented code and API interfaces.

## Feasibility Studies  

### Technical Perspective

From my experience, Flask provides an agile foundation for swiftly incorporating enhancements. The MVC separation and API abstractions promote loose coupling across layers. Load and stress testing reveals robust performance even on low-cost infrastructure.  

I have instrumented profiling hooks yielding optimization targets - chiefly introducing asynchronicity and query caching. Built-in Flask scaffolding permits quickly spinning up new modules. With prudent enhancements, I am confident of fulfilling projected capacity growth.

### Personal Value  

By open sourcing StockX, I hope to build an engaged user community through a free offering comparable to expensive trading platforms. This aligns with my priority of maximizing accessibility. Monetization would likely originate from premium features like customized analytics.  

I plan to regularly engage users for feedback on potential education-focused features that provide value proportionate to development costs and maintenance overhead. This user-centric ideation should sustain platform relevance.

### User Experience   

From my initial small-group trials, the intuitive workflows and visualizations accelerated understanding of trading concepts. Minor UX refinements post-feedback should further enhance learnability.

Feature flags help test-drive capabilities with subsets of users, allowing iterative refinement before global launch. The modular architecture and deployment automation aids rapid incremental updates.

Overall, StockX in its current state delivers on core objectives of education through simulation. Judicious user-centric enhancements rooted in technical and economic feasibility assessments should help cement long term viability.

## Source Code Integration  

As the sole developer, my observations and comments manifest directly in the implementation - clarifying rationale, highlighting improvement areas and more.  

For example, API interfaces contain:

```python
# Enforces query payload standards.  
# Validate against permitted args after enhancements
@app.route("/quote")   
def get_quote():
  ...
```

Such snippets document intents and assumptions during development aiding future maintainers. Plotly visualization components similarly contain schemas mapping data fields to chart axes.  

Integrating these source code insights should allow organically evolving documentation in sync with software enhancements. My inputs directly steer progress by unveiling developer reasoning.

## External APIs  

StockX leverages the following external APIs:  

### Alpha Vantage API  

Alpha Vantage provides realtime and historical stock data for building trading and analysis applications.  

**Capabilities**

- Realtime price quotes  
- Intraday and daily time series
- Historical data for equities, forex, crypto
- Technical indicators
- Company financials   
- Convert company name to stock symbol

**Endpoints**

I have integrated the following endpoints:


```
FUNCTION=SYMBOL_SEARCH
  - Lookup instrument symbol based on company name
  
PARAMETERS: keywords (company name), API key
```
**Usage**   

I leverage the SYMBOL_SEARCH endpoint to **convert a company name entered by the user (e.g. "Amazon") to its stock symbol (e.g. "AMZN") for fetching the quote and allowing stock trades**. This provides an intuitive search mechanism before redirecting users to the stock's home page..

**Endpoints**

I have integrated the following endpoints:

```  
FUNCTION=TIME_SERIES_INTRADAY
  - For 5-minute granularity intraday prices  
  
PARAMETERS: symbol, interval, datatype, API key
```

```
FUNCTION=SYMBOL_SEARCH
  - Lookup instrument symbol based on keywords
  
PARAMETERS: keywords, API key  
```
 

**Usage**   

I leverage the TIME_SERIES_INTRADAY endpoint to populate the historical price graphs. SYMBOL_SEARCH is used when users search for instruments on the explore page.  

**Authentication**  

Alpha Vantage uses API keys to authenticate each request. My subscription key with standard rate limits is configured on the server. 

**Client**  

The Python alpha_vantage library provides convenient access to the API from Flask route handlers.

### Twilio Verify API  

Twilio Verify enables sending one-time passcodes to validate user phone numbers during signup.  

**Capabilities**   

- Send OTP to phone via SMS/Voice  
- Validate code entered by user
- Configure OTP length, validity duration etc  

**Endpoints**  

```
/v2/Services/{ServiceSid}/Verifications 
  - Initiate verification request
  
/v2/Services/{ServiceSid}/VerificationChecks
  - Validate OTP entered by user  
```

**Authentication**   

Verify uses Twilio Account SID and Auth Token configured on the server.  

**Usage**   

I trigger phone verification flows during new user signup. This validates user-provided numbers.   

**Client**  

The Twilio Python SDK provides client objects to conveniently access the Verify API.

### Yahoo Finance API

Yahoo Finance API delivers historical equities data for charting and analysis.   

**Capabilities**     

- Historical stocks data   
- Quotes, price histories
- Fundamentals data  
- Screeners  

**Endpoints**   

I use the quote and historical price endpoints   

**Authentication**  

No authentication required     

**Usage**  

The historical price data populates the StockX technical charting modules.  

**Client**   

I leverage the yfinance Python client to access the API from Flask code.

## Security Measures  

Current measures like SSL encryption, password salting, input sanitization closely follow industry standards.   

Additionally, protections I am planning include:  

- Two Factor Authentication using Google Authenticator.  
- User Session Monitoring for simultaneous logins across geographic locations.  
- OWASP Protection against cross-site attacks, SQL injections etc.  

As a passionate open source contributor, I plan to collaborate with security researchers to implement cutting-edge protections proactively.   

## Conclusion  

In summary, StockX originated from my drive to educate investors protectively on market dynamics before financial exposure. The project fused my web development skills and trading knowledge into an accessible platform.  

Robust existing foundations coupled with pragmatically planned enhancements root the offering's growth in technical and economic viability. Prioritizing both user experience and security should sustain trust and relevance.   

Developer contributions are welcomed to realize the grand vision of establishing StockX as a global gold standard for trading education! This personalized document immortalizes my journey and motivations.

