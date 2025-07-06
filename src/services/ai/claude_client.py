"""
Claude AI Client for Fantasy Football Assistant

Handles integration with Anthropic's Claude API for natural language processing,
player analysis, and intelligent fantasy football recommendations.
"""

import asyncio
from typing import Dict, List, Any, Optional, Union
import json
import logging
from datetime import datetime

from anthropic import AsyncAnthropic
from ...config import settings

logger = logging.getLogger(__name__)


class ClaudeAIClient:
    """Client for interacting with Anthropic's Claude API for fantasy football intelligence"""
    
    def __init__(self):
        """Initialize Claude client with API key from settings"""
        if not settings.anthropic_api_key:
            logger.warning("Anthropic API key not configured - AI features will be limited")
            self.client = None
        else:
            self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        
        # Conversation history management
        self.conversations: Dict[str, List[Dict[str, str]]] = {}
        
        # Fantasy football context prompts
        self.system_prompts = {
            "general": self._get_general_system_prompt(),
            "player_analysis": self._get_player_analysis_prompt(),
            "trade_analysis": self._get_trade_analysis_prompt(),
            "draft_strategy": self._get_draft_strategy_prompt(),
            "lineup_optimization": self._get_lineup_optimization_prompt()
        }
    
    def _get_general_system_prompt(self) -> str:
        """Get the general system prompt for fantasy football assistance"""
        return """
You are an expert fantasy football analyst and advisor. You have deep knowledge of:

- NFL player statistics, trends, and performance patterns
- Fantasy football scoring systems (standard, PPR, half-PPR)
- Draft strategies, value-based drafting, and positional scarcity
- Waiver wire pickups and trade analysis
- Matchup analysis and start/sit decisions
- Injury impact and player usage trends

Your responses should be:
- Data-driven and analytical
- Clear and actionable
- Confident but acknowledge uncertainty when appropriate
- Tailored to the user's specific league settings and team needs
- Include reasoning behind recommendations

Always consider current week, season context, playoff implications, and league-specific factors.
Be concise but thorough in your analysis.
"""

    def _get_player_analysis_prompt(self) -> str:
        """Get system prompt for player-specific analysis"""
        return """
You are analyzing a specific NFL player for fantasy football purposes. Consider:

- Recent performance trends (last 3-4 weeks)
- Season-long statistics and consistency
- Usage patterns (targets, carries, red zone opportunities)
- Team context (offense quality, coaching, game script)
- Matchup factors (opponent defense, weather, venue)
- Injury status and impact
- Rest-of-season outlook

Provide analysis on:
1. Current fantasy value and role
2. Upcoming week outlook
3. Rest-of-season projection
4. Key factors to monitor
5. Confidence level in assessment
"""

    def _get_trade_analysis_prompt(self) -> str:
        """Get system prompt for trade evaluation"""
        return """
You are evaluating a fantasy football trade proposal. Analyze from multiple angles:

Team Context:
- Each team's roster construction and needs
- Current standings and playoff outlook
- Bye week considerations
- Depth at each position

Player Evaluation:
- Current season performance and trends
- Rest-of-season outlook and schedule
- Injury risk and durability
- Positional value and scarcity

Trade Analysis:
- Immediate impact vs long-term value
- Position of strength vs need
- Fair value assessment
- Risk/reward evaluation

Provide:
1. Trade recommendation (accept/decline/counter)
2. Analysis for each player involved
3. Impact on both teams
4. Suggested improvements or counters
5. Confidence level in assessment
"""

    def _get_draft_strategy_prompt(self) -> str:
        """Get system prompt for draft assistance"""
        return """
You are providing draft strategy and pick recommendations. Consider:

Draft Context:
- Current draft position and round
- Available players and their ADP
- Position runs and positional scarcity
- League scoring settings and roster requirements

Strategy Factors:
- Value-based drafting principles
- Positional tiers and drop-offs
- Bye week distribution
- Risk tolerance and ceiling/floor players
- League tendencies and opponent behavior

Recommendations should include:
1. Best player available at current pick
2. Position-specific needs assessment
3. Value opportunities and steals
4. Players to avoid at current ADP
5. Future round planning and targets
"""

    def _get_lineup_optimization_prompt(self) -> str:
        """Get system prompt for lineup decisions"""
        return """
You are optimizing fantasy lineups for maximum points. Analyze:

Player Factors:
- Recent performance and usage trends
- Matchup favorability (defense rankings, pace, game script)
- Injury status and questionable designations
- Weather conditions and venue factors
- Motivation factors (playoff implications, divisional games)

Strategic Considerations:
- Ceiling vs floor plays based on team needs
- Correlation plays (QB/WR, RB/Defense)
- Leverage opportunities in tournaments
- Risk management for cash games
- Late swap opportunities

Provide:
1. Optimal lineup recommendations
2. Start/sit reasoning for each position
3. Alternative options and pivot plays
4. Confidence levels for each decision
5. Key factors to monitor before kickoff
"""

    async def chat_completion(
        self, 
        message: str, 
        context: Optional[Dict[str, Any]] = None,
        conversation_id: Optional[str] = None,
        analysis_type: str = "general"
    ) -> Dict[str, Any]:
        """
        Send a message to Claude and get a response
        
        Args:
            message: User message/question
            context: Additional context (team data, player data, etc.)
            conversation_id: ID for conversation continuity
            analysis_type: Type of analysis (general, player_analysis, etc.)
            
        Returns:
            Dict containing response, confidence, and metadata
        """
        if not self.client:
            return {
                "response": "AI features are not available - Anthropic API key not configured",
                "confidence": 0.0,
                "conversation_id": conversation_id,
                "analysis_type": analysis_type,
                "timestamp": datetime.now().isoformat(),
                "usage": {
                    "input_tokens": 0,
                    "output_tokens": 0
                },
                "error": "api_not_configured"
            }
        
        try:
            # Build conversation history
            messages = []
            if conversation_id and conversation_id in self.conversations:
                messages.extend(self.conversations[conversation_id])
            
            # Add context to message if provided
            enhanced_message = self._enhance_message_with_context(message, context)
            messages.append({"role": "user", "content": enhanced_message})
            
            # Get appropriate system prompt
            system_prompt = self.system_prompts.get(analysis_type, self.system_prompts["general"])
            
            # For development/testing without API key, return mock response
            if not self.client or not hasattr(self.client, 'messages'):
                logger.warning("Anthropic client not properly initialized - returning mock response")
                response_text = self._generate_mock_response(message, analysis_type)
                confidence = 0.85
                usage = {"input_tokens": 0, "output_tokens": 0}
            else:
                # Make API call to Claude
                response = await self.client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=2000,
                    temperature=0.1,
                    system=system_prompt,
                    messages=messages
                )
                response_text = response.content[0].text if response.content else "No response generated"
                # Calculate confidence based on response characteristics
                confidence = self._calculate_response_confidence(response_text, context)
                usage = {
                    "input_tokens": response.usage.input_tokens if hasattr(response, 'usage') else 0,
                    "output_tokens": response.usage.output_tokens if hasattr(response, 'usage') else 0
                }
            
            # Store conversation history
            if conversation_id:
                if conversation_id not in self.conversations:
                    self.conversations[conversation_id] = []
                self.conversations[conversation_id].extend([
                    {"role": "user", "content": enhanced_message},
                    {"role": "assistant", "content": response_text}
                ])
                
                # Limit conversation history to last 10 exchanges
                if len(self.conversations[conversation_id]) > 20:
                    self.conversations[conversation_id] = self.conversations[conversation_id][-20:]
            
            return {
                "response": response_text,
                "confidence": confidence,
                "conversation_id": conversation_id,
                "analysis_type": analysis_type,
                "timestamp": datetime.now().isoformat(),
                "usage": usage
            }
            
        except Exception as e:
            logger.error(f"Claude API error: {e}")
            return {
                "response": f"Sorry, I encountered an error processing your request: {str(e)}",
                "confidence": 0.0,
                "conversation_id": conversation_id,
                "analysis_type": analysis_type,
                "timestamp": datetime.now().isoformat(),
                "usage": {
                    "input_tokens": 0,
                    "output_tokens": 0
                },
                "error": "api_error",
                "error_details": str(e)
            }
    
    async def analyze_player(
        self, 
        player_data: Dict[str, Any],
        analysis_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze a specific player for fantasy football value
        
        Args:
            player_data: Player statistics and information
            analysis_context: League settings, team context, etc.
            
        Returns:
            Dict containing player analysis and recommendations
        """
        # Build analysis prompt
        prompt = f"""
Analyze this player for fantasy football:

Player: {player_data.get('name', 'Unknown')}
Position: {player_data.get('position', 'Unknown')}
Team: {player_data.get('team', 'Unknown')}

Recent Stats (last 4 weeks):
{self._format_player_stats(player_data.get('recent_stats', {}))}

Season Stats:
{self._format_player_stats(player_data.get('season_stats', {}))}

Additional Context:
{json.dumps(analysis_context or {}, indent=2)}

Provide a comprehensive analysis including current value, upcoming outlook, and recommendations.
"""
        
        return await self.chat_completion(
            message=prompt,
            context={"player_data": player_data, "analysis_context": analysis_context},
            analysis_type="player_analysis"
        )
    
    async def analyze_trade(
        self, 
        trade_data: Dict[str, Any],
        team_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze a trade proposal
        
        Args:
            trade_data: Trade details (players involved, teams)
            team_context: Team rosters, standings, needs
            
        Returns:
            Dict containing trade analysis and recommendation
        """
        prompt = f"""
Evaluate this trade proposal:

Trade Details:
{json.dumps(trade_data, indent=2)}

Team Context:
{json.dumps(team_context or {}, indent=2)}

Provide a detailed trade analysis with recommendation, reasoning, and potential improvements.
"""
        
        return await self.chat_completion(
            message=prompt,
            context={"trade_data": trade_data, "team_context": team_context},
            analysis_type="trade_analysis"
        )
    
    async def generate_weekly_insights(
        self, 
        team_data: Dict[str, Any],
        week: int
    ) -> Dict[str, Any]:
        """
        Generate weekly insights and recommendations for a team
        
        Args:
            team_data: Team roster, recent performance, league context
            week: Current NFL week
            
        Returns:
            Dict containing weekly insights and action items
        """
        prompt = f"""
Generate weekly insights for Week {week}:

Team Data:
{json.dumps(team_data, indent=2)}

Provide:
1. Key insights for the upcoming week
2. Start/sit recommendations with reasoning
3. Waiver wire targets to consider
4. Trade opportunities to explore
5. Long-term strategy considerations

Focus on actionable advice that can improve the team's chances of winning.
"""
        
        return await self.chat_completion(
            message=prompt,
            context={"team_data": team_data, "week": week},
            analysis_type="general"
        )
    
    def _enhance_message_with_context(self, message: str, context: Optional[Dict[str, Any]]) -> str:
        """Add relevant context to the user message"""
        if not context:
            return message
        
        enhanced = message + "\n\nRelevant Context:\n"
        
        # Add league settings if available
        if "league_settings" in context:
            enhanced += f"League Settings: {json.dumps(context['league_settings'], indent=2)}\n"
        
        # Add current week if available
        if "current_week" in context:
            enhanced += f"Current Week: {context['current_week']}\n"
        
        # Add team context if available
        if "team_context" in context:
            enhanced += f"Team Context: {json.dumps(context['team_context'], indent=2)}\n"
        
        return enhanced
    
    def _format_player_stats(self, stats: Dict[str, Any]) -> str:
        """Format player statistics for display"""
        if not stats:
            return "No statistics available"
        
        formatted = []
        for key, value in stats.items():
            formatted.append(f"{key}: {value}")
        
        return "\n".join(formatted)
    
    def _calculate_response_confidence(self, response: str, context: Optional[Dict[str, Any]]) -> float:
        """Calculate confidence score based on response characteristics"""
        confidence = 0.7  # Base confidence
        
        # Increase confidence for longer, more detailed responses
        if len(response) > 500:
            confidence += 0.1
        
        # Increase confidence if context was provided
        if context:
            confidence += 0.1
        
        # Look for uncertainty indicators in response
        uncertainty_words = ["might", "could", "possibly", "uncertain", "unclear"]
        uncertainty_count = sum(1 for word in uncertainty_words if word.lower() in response.lower())
        confidence -= uncertainty_count * 0.05
        
        # Look for confidence indicators
        confidence_words = ["definitely", "clearly", "strong", "confident", "recommend"]
        confidence_count = sum(1 for word in confidence_words if word.lower() in response.lower())
        confidence += confidence_count * 0.02
        
        return max(0.0, min(1.0, confidence))
    
    def clear_conversation(self, conversation_id: str):
        """Clear conversation history for a specific conversation"""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
    
    def get_conversation_summary(self, conversation_id: str) -> Dict[str, Any]:
        """Get summary of conversation history"""
        if conversation_id not in self.conversations:
            return {"messages": 0, "exists": False}
        
        messages = self.conversations[conversation_id]
        return {
            "messages": len(messages),
            "exists": True,
            "last_interaction": messages[-1]["content"][:100] + "..." if messages else None
        }

    def _generate_mock_response(self, message: str, analysis_type: str) -> str:
        """Generate mock response for development/testing"""
        mock_responses = {
            "general": f"I understand you're asking about: {message[:50]}... Based on current fantasy football trends, I would recommend considering factors like recent performance, matchups, and injury reports. This is a mock response for development purposes.",
            "player_analysis": f"Analyzing player based on your query: {message[:50]}... Key factors to consider include recent usage, target share, and upcoming matchups. This is a mock response for development purposes.",
            "trade_analysis": f"Evaluating trade scenario: {message[:50]}... Consider player values, team needs, and rest-of-season outlook. This is a mock response for development purposes.",
            "draft_strategy": f"Draft strategy for: {message[:50]}... Focus on value-based drafting and positional scarcity. This is a mock response for development purposes.",
            "lineup_optimization": f"Optimizing lineup based on: {message[:50]}... Consider matchups and projected points. This is a mock response for development purposes."
        }
        
        return mock_responses.get(analysis_type, mock_responses["general"])


# Global AI client instance
ai_client = ClaudeAIClient()