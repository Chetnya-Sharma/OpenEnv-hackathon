#!/usr/bin/env python3
"""
Backend API Testing for SQL Review Environment
Tests all OpenEnv endpoints and validates functionality
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, Any, List

class SQLReviewAPITester:
    def __init__(self, base_url="https://db-query-reviewer.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.env_state = None
        self.current_task_id = None
        
    def log(self, message: str):
        """Log test messages with timestamp"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
        
    def run_test(self, name: str, method: str, endpoint: str, expected_status: int = 200, 
                 data: Dict = None, validate_func=None) -> tuple:
        """Run a single API test with validation"""
        url = f"{self.base_url}/api/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        self.tests_run += 1
        self.log(f"🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            success = response.status_code == expected_status
            response_data = {}
            
            try:
                response_data = response.json()
            except:
                response_data = {"raw_response": response.text}
                
            if success and validate_func:
                validation_result = validate_func(response_data)
                if not validation_result:
                    success = False
                    self.log(f"❌ Validation failed for {name}")
                    
            if success:
                self.tests_passed += 1
                self.log(f"✅ {name} - Status: {response.status_code}")
            else:
                self.log(f"❌ {name} - Expected {expected_status}, got {response.status_code}")
                if response_data.get('error'):
                    self.log(f"   Error: {response_data['error']}")
                    
            return success, response_data
            
        except Exception as e:
            self.log(f"❌ {name} - Exception: {str(e)}")
            return False, {"error": str(e)}
    
    def validate_health(self, data: Dict) -> bool:
        """Validate health endpoint response"""
        return (data.get('status') == 'ok' and 
                data.get('version') == '1.0.0')
    
    def validate_reset_response(self, data: Dict) -> bool:
        """Validate env/reset response structure"""
        if 'observation' not in data or 'info' not in data:
            return False
            
        obs = data['observation']
        info = data['info']
        
        # Check observation structure
        required_obs_fields = ['queries', 'current_step', 'task_id', 'reviewed_count', 
                              'pending_count', 'last_action_result', 'session_stats', 'done']
        for field in required_obs_fields:
            if field not in obs:
                self.log(f"Missing observation field: {field}")
                return False
                
        # Check info structure
        required_info_fields = ['task_id', 'max_steps', 'num_queries']
        for field in required_info_fields:
            if field not in info:
                self.log(f"Missing info field: {field}")
                return False
                
        # Validate ground truth is hidden in observation
        if obs.get('queries'):
            for query in obs['queries']:
                ground_truth_fields = ['has_injection_risk', 'has_performance_issue', 
                                     'has_logic_bug', 'correct_verdict']
                for field in ground_truth_fields:
                    if field in query:
                        self.log(f"Ground truth field {field} found in observation!")
                        return False
                        
        return True
    
    def validate_step_response(self, data: Dict) -> bool:
        """Validate env/step response structure"""
        required_fields = ['observation', 'reward', 'done', 'info']
        for field in required_fields:
            if field not in data:
                self.log(f"Missing step response field: {field}")
                return False
                
        # Reward should be a number
        if not isinstance(data['reward'], (int, float)):
            self.log(f"Reward is not a number: {data['reward']}")
            return False
            
        return True
    
    def validate_state_response(self, data: Dict) -> bool:
        """Validate env/state response includes ground truth"""
        if 'queries' not in data:
            return False
            
        # State should include ground truth fields
        for query_id, query in data['queries'].items():
            ground_truth_fields = ['has_injection_risk', 'has_performance_issue', 
                                 'has_logic_bug', 'correct_verdict']
            for field in ground_truth_fields:
                if field not in query:
                    self.log(f"Ground truth field {field} missing from state!")
                    return False
                    
        return True
    
    def validate_tasks_response(self, data: List) -> bool:
        """Validate env/tasks response structure"""
        if not isinstance(data, list) or len(data) != 3:
            self.log(f"Expected 3 tasks, got {len(data) if isinstance(data, list) else 'non-list'}")
            return False
            
        expected_tasks = ['single_review', 'batch_review', 'pipeline_review']
        found_tasks = [task.get('id') for task in data]
        
        for expected in expected_tasks:
            if expected not in found_tasks:
                self.log(f"Missing expected task: {expected}")
                return False
                
        # Validate task structure
        for task in data:
            required_fields = ['id', 'name', 'difficulty', 'max_steps', 'description', 'num_queries']
            for field in required_fields:
                if field not in task:
                    self.log(f"Missing task field {field} in task {task.get('id')}")
                    return False
                    
        return True
    
    def test_health(self) -> bool:
        """Test GET /api/health"""
        success, data = self.run_test(
            "Health Check", "GET", "health", 200, 
            validate_func=self.validate_health
        )
        return success
    
    def test_env_reset_single(self) -> bool:
        """Test POST /api/env/reset with single_review task"""
        success, data = self.run_test(
            "Reset Single Review", "POST", "env/reset", 200,
            data={"task_id": "single_review"},
            validate_func=self.validate_reset_response
        )
        if success:
            self.env_state = data
            self.current_task_id = "single_review"
            # Validate single_review has 1 query
            if data['info']['num_queries'] != 1:
                self.log(f"❌ Single review should have 1 query, got {data['info']['num_queries']}")
                return False
        return success
    
    def test_env_reset_batch(self) -> bool:
        """Test POST /api/env/reset with batch_review task"""
        success, data = self.run_test(
            "Reset Batch Review", "POST", "env/reset", 200,
            data={"task_id": "batch_review"},
            validate_func=self.validate_reset_response
        )
        if success:
            # Validate batch_review has 8 queries
            if data['info']['num_queries'] != 8:
                self.log(f"❌ Batch review should have 8 queries, got {data['info']['num_queries']}")
                return False
        return success
    
    def test_env_reset_pipeline(self) -> bool:
        """Test POST /api/env/reset with pipeline_review task"""
        success, data = self.run_test(
            "Reset Pipeline Review", "POST", "env/reset", 200,
            data={"task_id": "pipeline_review"},
            validate_func=self.validate_reset_response
        )
        if success:
            # Validate pipeline_review has 15 queries
            if data['info']['num_queries'] != 15:
                self.log(f"❌ Pipeline review should have 15 queries, got {data['info']['num_queries']}")
                return False
            # Check for urgent queries
            urgent_count = sum(1 for q in data['observation']['queries'] if q.get('is_urgent', False))
            if urgent_count == 0:
                self.log(f"❌ Pipeline review should have some urgent queries, found {urgent_count}")
                return False
        return success
    
    def test_env_reset_default(self) -> bool:
        """Test POST /api/env/reset with empty body (should default to single_review)"""
        success, data = self.run_test(
            "Reset Default Task", "POST", "env/reset", 200,
            data={},
            validate_func=self.validate_reset_response
        )
        if success:
            if data['info']['task_id'] != 'single_review':
                self.log(f"❌ Default task should be single_review, got {data['info']['task_id']}")
                return False
        return success
    
    def test_env_step_valid(self) -> bool:
        """Test POST /api/env/step with valid action"""
        # First reset to single_review
        self.test_env_reset_single()
        
        if not self.env_state or not self.env_state['observation']['queries']:
            self.log("❌ No queries available for step test")
            return False
            
        query = self.env_state['observation']['queries'][0]
        action = {
            "action_type": "approve",
            "query_id": query['query_id'],
            "verdict": "approve",
            "issues_found": ["no_issues"],
            "suggested_fix": "",
            "confidence": 0.8
        }
        
        success, data = self.run_test(
            "Step Valid Action", "POST", "env/step", 200,
            data=action,
            validate_func=self.validate_step_response
        )
        
        if success:
            # Store for grader variation test
            self.first_reward = data['reward']
            
        return success
    
    def test_env_step_different_action(self) -> bool:
        """Test POST /api/env/step with different action to verify grader variation"""
        # Reset again
        self.test_env_reset_single()
        
        if not self.env_state or not self.env_state['observation']['queries']:
            self.log("❌ No queries available for step test")
            return False
            
        query = self.env_state['observation']['queries'][0]
        action = {
            "action_type": "reject",
            "query_id": query['query_id'],
            "verdict": "reject",
            "issues_found": ["sql_injection", "performance"],
            "suggested_fix": "Use parameterized queries to prevent SQL injection",
            "confidence": 0.9
        }
        
        success, data = self.run_test(
            "Step Different Action", "POST", "env/step", 200,
            data=action,
            validate_func=self.validate_step_response
        )
        
        if success and hasattr(self, 'first_reward'):
            # Check if rewards are different (grader produces varied scores)
            if data['reward'] == self.first_reward:
                self.log(f"⚠️  Warning: Same reward for different actions ({data['reward']})")
            else:
                self.log(f"✅ Grader produces varied scores: {self.first_reward} vs {data['reward']}")
                
        return success
    
    def test_env_state(self) -> bool:
        """Test GET /api/env/state"""
        success, data = self.run_test(
            "Get Environment State", "GET", "env/state", 200,
            validate_func=self.validate_state_response
        )
        return success
    
    def test_env_tasks(self) -> bool:
        """Test GET /api/env/tasks"""
        success, data = self.run_test(
            "Get Task Definitions", "GET", "env/tasks", 200,
            validate_func=self.validate_tasks_response
        )
        return success
    
    def test_env_queries(self) -> bool:
        """Test GET /api/env/queries"""
        success, data = self.run_test(
            "Get Query Statistics", "GET", "env/queries", 200
        )
        if success:
            # Validate structure
            if 'total' not in data or 'categories' not in data:
                self.log("❌ Missing total or categories in queries response")
                return False
            if data['total'] < 50:  # Should have 50+ queries
                self.log(f"❌ Expected 50+ queries, got {data['total']}")
                return False
        return success
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all backend API tests"""
        self.log("🚀 Starting SQL Review Environment API Tests")
        self.log(f"Testing against: {self.base_url}")
        
        test_results = {}
        
        # Core API tests
        test_results['health'] = self.test_health()
        test_results['env_reset_single'] = self.test_env_reset_single()
        test_results['env_reset_batch'] = self.test_env_reset_batch()
        test_results['env_reset_pipeline'] = self.test_env_reset_pipeline()
        test_results['env_reset_default'] = self.test_env_reset_default()
        test_results['env_step_valid'] = self.test_env_step_valid()
        test_results['env_step_different'] = self.test_env_step_different_action()
        test_results['env_state'] = self.test_env_state()
        test_results['env_tasks'] = self.test_env_tasks()
        test_results['env_queries'] = self.test_env_queries()
        
        # Summary
        self.log(f"\n📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        failed_tests = [name for name, passed in test_results.items() if not passed]
        if failed_tests:
            self.log(f"❌ Failed tests: {', '.join(failed_tests)}")
        else:
            self.log("✅ All tests passed!")
            
        return {
            "total_tests": self.tests_run,
            "passed_tests": self.tests_passed,
            "failed_tests": failed_tests,
            "success_rate": self.tests_passed / self.tests_run if self.tests_run > 0 else 0,
            "test_results": test_results
        }

def main():
    """Main test execution"""
    tester = SQLReviewAPITester()
    results = tester.run_all_tests()
    
    # Return appropriate exit code
    return 0 if results["success_rate"] == 1.0 else 1

if __name__ == "__main__":
    sys.exit(main())